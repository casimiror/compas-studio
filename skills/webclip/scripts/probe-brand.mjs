#!/usr/bin/env node
// Best-effort scan of the CURRENT project (cwd) for brand tokens and assets a webclip
// composition could reuse. Never fails hard — prints whatever it finds as JSON and
// exits 0 even on an empty project. The caller (the webclip skill) is responsible for
// presenting this to the user for confirmation before building anything with it.

import { promises as fs } from 'node:fs';
import path from 'node:path';

const CWD = process.cwd();
const HEX_RE = /#[0-9a-fA-F]{6}\b/g;
const FONT_RE = /font-?family['":\s]*['"]?([A-Za-z0-9 ]+)['"]?/gi;
const IGNORE_DIRS = new Set(['node_modules', '.git', 'build', 'dist', '.next', '.dart_tool', 'Pods']);

async function walk(dir, depth, onFile) {
  if (depth < 0) return;
  let entries;
  try { entries = await fs.readdir(dir, { withFileTypes: true }); } catch { return; }
  for (const entry of entries) {
    if (entry.name.startsWith('.') && entry.name !== '.env.example') continue;
    if (IGNORE_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) await walk(full, depth - 1, onFile);
    else await onFile(full, entry.name);
  }
}

async function findStyleGuideDocs() {
  const hits = [];
  await walk(path.join(CWD, 'docs'), 6, (full, name) => {
    if (/style.*guide|design.*(tokens|system)/i.test(name) && name.endsWith('.md')) {
      hits.push(full);
    }
  });
  // also check CLAUDE.md for a design/tokens section
  for (const candidate of ['CLAUDE.md', path.join(CWD, '.claude', 'CLAUDE.md')]) {
    try { await fs.access(candidate); hits.push(candidate); } catch {}
  }
  return hits;
}

async function extractTokens(files) {
  const colors = new Set();
  const fonts = new Set();
  for (const f of files) {
    let text;
    try { text = await fs.readFile(f, 'utf8'); } catch { continue; }
    for (const m of text.matchAll(HEX_RE)) colors.add(m[0]);
    for (const m of text.matchAll(FONT_RE)) {
      const name = m[1].trim();
      if (name && name.length < 40) fonts.add(name);
    }
  }
  return { colors: [...colors].slice(0, 24), fonts: [...fonts].slice(0, 10) };
}

async function findLogos() {
  const dirs = ['assets/logo', 'assets/images/logo', 'public/logo', 'src/assets/logo', 'branding', 'assets/brand'];
  const found = [];
  for (const d of dirs) {
    const full = path.join(CWD, d);
    try {
      const entries = await fs.readdir(full);
      for (const e of entries) {
        if (/logo/i.test(e) && /\.(png|svg|webp|jpg|jpeg)$/i.test(e)) found.push(path.join(full, e));
      }
    } catch {}
  }
  // fallback: shallow search anywhere under assets/ or public/ for *logo*
  if (found.length === 0) {
    for (const base of ['assets', 'public', 'src']) {
      await walk(path.join(CWD, base), 3, (full, name) => {
        if (/logo/i.test(name) && /\.(png|svg|webp|jpg|jpeg)$/i.test(name)) found.push(full);
      });
    }
  }
  return [...new Set(found)].slice(0, 10);
}

async function findScreenshots() {
  const dirs = ['assets/images/screenshots', 'assets/screenshots', 'public/images/screenshots', 'screenshots', 'assets/images'];
  const found = [];
  for (const d of dirs) {
    const full = path.join(CWD, d);
    try {
      const entries = await fs.readdir(full, { withFileTypes: true });
      for (const e of entries) {
        if (e.isFile() && /\.(png|jpg|jpeg|webp)$/i.test(e.name)) found.push(path.join(full, e.name));
      }
    } catch {}
    if (found.length >= 20) break;
  }
  return [...new Set(found)].slice(0, 20);
}

async function main() {
  const styleDocs = await findStyleGuideDocs();
  const tokens = await extractTokens(styleDocs);
  const logos = await findLogos();
  const screenshots = await findScreenshots();

  const summary = {
    cwd: CWD,
    styleGuideDocs: styleDocs,
    colors: tokens.colors,
    fonts: tokens.fonts,
    logos,
    screenshots,
    confidence: styleDocs.length || logos.length || screenshots.length ? 'found-material' : 'empty-scan',
  };

  console.log(JSON.stringify(summary, null, 2));
}

main().catch((err) => {
  console.error(JSON.stringify({ error: String(err), confidence: 'scan-failed' }));
  process.exit(0);
});
