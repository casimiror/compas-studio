#!/usr/bin/env node
// Render a webclip HTML composition to a real video file.
//
// Usage:
//   node render.mjs <file.html> --out out.mp4 [--width 1080] [--height 1920]
//     [--fps 30] [--duration 12.5] [--audio track.mp3] [--transparent] [--format gif]
//     [--concurrency 4]
//
// Mechanism: serves the HTML's directory over http:// (avoids file:// CORS/font
// issues), waits for document.fonts + window.__clip, then drives window.__clip.seek(t)
// frame-by-frame (deterministic — not real-time capture) while screenshotting each
// frame to a temp file, then encodes with ffmpeg.
//
// Perf note: headless Chromium on most dev machines rasterizes via a software GPU
// (swiftshader) — screenshot capture is IPC/compositor-bound, not CPU-bound (observed
// ~18% CPU during a single-page render). Frames are split into `--concurrency` shards,
// each captured by its own browser page/tab concurrently, which scales close to
// linearly since the bottleneck isn't contended CPU work. JPEG frames (used whenever
// `--transparent` isn't set) also capture noticeably faster than PNG at this resolution.

import { chromium } from 'playwright';
import http from 'node:http';
import { createReadStream, promises as fs } from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import os from 'node:os';

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.gif': 'image/gif',
  '.woff': 'font/woff', '.woff2': 'font/woff2', '.mp3': 'audio/mpeg', '.json': 'application/json',
};

function parseArgs(argv) {
  const args = { width: 1080, height: 1920, fps: 30, concurrency: Math.max(1, Math.min(4, os.cpus().length)) };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out') args.out = argv[++i];
    else if (a === '--width') args.width = Number(argv[++i]);
    else if (a === '--height') args.height = Number(argv[++i]);
    else if (a === '--fps') args.fps = Number(argv[++i]);
    else if (a === '--duration') args.duration = Number(argv[++i]);
    else if (a === '--audio') args.audio = argv[++i];
    else if (a === '--transparent') args.transparent = true;
    else if (a === '--format') args.format = argv[++i];
    else if (a === '--concurrency') args.concurrency = Math.max(1, Number(argv[++i]));
    else positional.push(a);
  }
  args.input = positional[0];
  return args;
}

function serveDir(rootDir) {
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent(req.url.split('?')[0]);
    const filePath = path.join(rootDir, urlPath === '/' ? '/index.html' : urlPath);
    if (!filePath.startsWith(rootDir)) { res.writeHead(403); res.end(); return; }
    fs.stat(filePath).then((stat) => {
      if (!stat.isFile()) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath)] || 'application/octet-stream' });
      createReadStream(filePath).pipe(res);
    }).catch(() => { res.writeHead(404); res.end(); });
  });
  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => resolve({ server, port: server.address().port }));
  });
}

function run(cmd, cmdArgs) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, cmdArgs, { stdio: ['ignore', 'pipe', 'pipe'] });
    let stderr = '';
    p.stderr.on('data', (d) => { stderr += d.toString(); });
    p.on('close', (code) => code === 0 ? resolve() : reject(new Error(`${cmd} exited ${code}\n${stderr}`)));
  });
}

async function openReadyPage(browser, port, fileName, width, height) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  await page.goto(`http://127.0.0.1:${port}/${fileName}`, { waitUntil: 'load' });
  await page.evaluate(async () => { if (document.fonts) await document.fonts.ready; });
  // Wait for <img> elements too: a frame captured before an image decodes comes out blank.
  await page.evaluate(() => Promise.all([...document.images].map((img) => (img.complete
    ? null : new Promise((r) => { img.addEventListener('load', r, { once: true }); img.addEventListener('error', r, { once: true }); }))))
    .then(() => {}));
  await page.waitForFunction(
    () => typeof window.__clip !== 'undefined'
      && typeof window.__clip.seek === 'function'
      && typeof window.__clip.duration === 'function',
    { timeout: 15000 }
  );
  // Tell any self-driven preview loop in the composition to stop ticking — it must
  // check this flag itself (composition-contract.md). `gsap.ticker.sleep()` was tried
  // here first and does NOT reliably stop an already-playing timeline (confirmed by
  // isolated testing: a timeline kept auto-restarting with the ticker "asleep"), so
  // there is no way to force this from the render side — it's on the composition to
  // cooperate. Without that cooperation, a composition that auto-plays/loops for human
  // preview keeps advancing in real time *underneath* our deterministic seeks — the
  // two drivers race for every captured frame, and on a slow capture (minutes of
  // wall-clock time for a few seconds of timeline) the output comes out flickering /
  // stuck on whatever the live loop last drew instead of the requested frame
  // (confirmed rendering the Compas acceptance clip).
  await page.evaluate(() => { window.__renderMode = true; });
  return page;
}

async function captureFrames(page, frameIndices, fps, tmpDir, ext, screenshotType, transparent) {
  for (const i of frameIndices) {
    const t = i / fps;
    // Block body: GSAP's .seek() returns the timeline itself (for chaining). An
    // arrow function with an expression body would return that value from
    // evaluate(), forcing Playwright to serialize the whole (circular, huge)
    // timeline object back to Node on every single frame — this was the real cause
    // of both the extreme slowness and the intermittent hangs found while building
    // this skill, not a timing race. Never let a per-frame evaluate() return
    // anything beyond a small plain value.
    await page.evaluate((time) => { window.__clip.seek(time); }, t);
    // A seek can set video.currentTime; capture only after every <video> has landed on its frame.
    await page.evaluate(() => Promise.all([...document.querySelectorAll('video')].map((v) => (v.seeking
      ? new Promise((r) => v.addEventListener('seeked', r, { once: true })) : null))).then(() => {}));
    const frameFile = path.join(tmpDir, `frame_${String(i).padStart(5, '0')}.${ext}`);
    const opts = { path: frameFile, omitBackground: !!transparent };
    if (screenshotType === 'jpeg') opts.type = 'jpeg', opts.quality = 92;
    await page.screenshot(opts);
  }
}

function splitIntoShards(totalFrames, shardCount) {
  const shards = Array.from({ length: shardCount }, () => []);
  for (let i = 0; i < totalFrames; i++) shards[i % shardCount].push(i);
  return shards.filter((s) => s.length > 0);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.input || !args.out) {
    console.error('Usage: node render.mjs <file.html> --out <out.mp4> [--width N] [--height N] [--fps N] [--duration S] [--audio track.mp3] [--concurrency N]');
    process.exit(1);
  }

  const inputAbs = path.resolve(args.input);
  const rootDir = path.dirname(inputAbs);
  const fileName = path.basename(inputAbs);
  const outAbs = path.resolve(args.out);

  const { server, port } = await serveDir(rootDir);
  const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'webclip-'));

  // PNG keeps real alpha for --transparent exports; JPEG is faster to capture/encode
  // and is fine for opaque clips, which is the common case.
  const ext = args.transparent ? 'png' : 'jpg';
  const screenshotType = args.transparent ? 'png' : 'jpeg';

  let browser;
  const pages = [];
  try {
    const t0 = Date.now();
    browser = await chromium.launch();

    const bootstrapPage = await openReadyPage(browser, port, fileName, args.width, args.height);
    pages.push(bootstrapPage);

    const duration = args.duration ?? await bootstrapPage.evaluate(() => window.__clip.duration());
    const totalFrames = Math.max(1, Math.round(duration * args.fps));
    const shardCount = Math.min(args.concurrency, totalFrames);

    console.log(`Rendering ${totalFrames} frames (${duration.toFixed(2)}s @ ${args.fps}fps, ${args.width}x${args.height}, concurrency=${shardCount})...`);

    for (let i = 1; i < shardCount; i++) {
      pages.push(await openReadyPage(browser, port, fileName, args.width, args.height));
    }

    const shards = splitIntoShards(totalFrames, shardCount);
    await Promise.all(shards.map((indices, i) => captureFrames(pages[i], indices, args.fps, tmpDir, ext, screenshotType, args.transparent)));

    await browser.close();
    browser = null;

    const captureSeconds = (Date.now() - t0) / 1000;
    console.log(`Captured ${totalFrames} frames in ${captureSeconds.toFixed(1)}s (${(totalFrames / captureSeconds).toFixed(1)} fps captured).`);

    const format = args.format || path.extname(outAbs).slice(1) || 'mp4';
    const ffArgs = ['-y', '-framerate', String(args.fps), '-i', path.join(tmpDir, `frame_%05d.${ext}`)];
    if (args.audio) ffArgs.push('-i', path.resolve(args.audio), '-shortest');

    if (format === 'gif') {
      ffArgs.push('-vf', `fps=${args.fps},scale=${args.width}:-1:flags=lanczos`, outAbs);
    } else if (format === 'webm' && args.transparent) {
      ffArgs.push('-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-crf', '30', '-b:v', '0', outAbs);
    } else if (format === 'webm') {
      ffArgs.push('-c:v', 'libvpx-vp9', '-pix_fmt', 'yuv420p', '-crf', '30', '-b:v', '0', outAbs);
    } else {
      ffArgs.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18');
      if (args.audio) ffArgs.push('-c:a', 'aac');
      ffArgs.push(outAbs);
    }

    console.log(`Encoding with: ffmpeg ${ffArgs.join(' ')}`);
    await run('ffmpeg', ffArgs);

    const totalSeconds = (Date.now() - t0) / 1000;
    console.log(`Done -> ${outAbs} (${args.width}x${args.height}, ${args.fps}fps, ${duration.toFixed(2)}s) in ${totalSeconds.toFixed(1)}s total.`);
  } finally {
    for (const p of pages) { try { await p.close(); } catch {} }
    if (browser) await browser.close();
    server.close();
    await fs.rm(tmpDir, { recursive: true, force: true });
  }
}

main().catch((err) => { console.error(err); process.exit(1); });
