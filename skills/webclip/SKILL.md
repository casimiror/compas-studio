---
name: webclip
description: >
  Build a short branded promo/explainer video as a single self-contained HTML/CSS/JS
  (GSAP) composition and render it to a real .mp4/.webm/.gif with Playwright + ffmpeg.
  Lightweight alternative to /hyperframes — no brief interview, no scaffolded project,
  no player-runtime contract. Use when the ask is "quick animated clip / branded video
  / logo sting / promo for X, built with plain HTML+JS" and a full narrated multi-scene
  HyperFrames production would be overkill. Route narrated, multi-minute, or caption/
  talking-head work to /hyperframes instead.
---

# webclip

> `<skills>` is the folder where the skills are installed (e.g. `~/.claude/skills` or the project's `.claude/skills`). Compas Studio skills are installed together, so one can call another's scripts.

A quick way to turn a project's real design tokens and real assets (logo, screenshots,
product shots) into a short animated video — preview instantly in a browser, render to
a real video file only when it's ready. Built to avoid the overhead of the full
HyperFrames brief/interview pipeline for simple branded clips.

## When to use this vs `/hyperframes`

| Use `webclip` when... | Use `/hyperframes` when... |
| --- | --- |
| The user wants a quick HTML/JS-built clip, explicitly or implicitly ("hazlo tú en JS") | The user wants a narrated, multi-scene, or longer production |
| A handful of scenes, ~5–30s, silent or with a simple music bed | Captions on real footage, talking-head overlays, music-synced edits |
| The project already has a style guide / logo / screenshots to pull from | Heavy asset sourcing, voiceover, transcription |

If the request clearly wants the full brief/storyboard/review-loop treatment, prefer
`/hyperframes` instead — don't reimplement its interview here.

## Environment restriction

Rendering (`render.mjs`) and browser preview (`open file.html`) run Chromium. If the user's rules
(`CLAUDE.md`, hooks) forbid browsers on the current account or machine, don't run them: you may
still write the composition HTML; tell the user where to preview and render.

## Workflow

### 1. Brand intake (assisted — never silent, never a full interview)

Run the probe from the target project's root:

```bash
node <skills>/webclip/scripts/probe-brand.mjs
```

It best-effort scans the current project for:
- a style guide / design-tokens doc (colors + font names)
- a logo (`*logo*.{png,svg}` under common asset dirs)
- a handful of screenshots / product shots

It prints a compact JSON summary. **Present this to the user as a short confirmation**
(e.g. via `AskUserQuestion`) before writing any composition — "found these colors / this
logo / these N screenshots, want me to use them, swap any, or add something else?" Never
proceed on an empty or low-confidence scan without asking; never turn this into a full
multi-question interview either — one confirmation round is enough.

If a scene needs an image/icon/logo variant that doesn't exist in the project, don't
generate it here — suggest the user run `/design` (logo/icon/banner generation) or
`/media-use` (resolve-or-generate), then treat the result as just another confirmed
asset to drop next to the HTML. Same for a Canva-made export or a Figma-sourced asset
(`/figma`) — they all land the same way: a confirmed file, copied alongside the HTML.

### 2. Scene plan — ask purpose first

Ask **what the video is for** before anything else; that one answer implies most of the
rest instead of asking each separately:

- Reel/Story (Instagram/TikTok) or WhatsApp status → vertical 9:16, ~10–15s, punchy, one CTA max
- Demo interno / para el equipo → horizontal or vertical, can run longer, favor real
  screenshots over flash/sweep effects, less "ad" energy
- Anuncio / CTA → needs a clear call-to-action beat near the end
- Loop para una pantalla o landing page → no hard outro; the last frame should tile
  cleanly back into the first

Then ask only what's not already implied: the one message/subject, and whether this is
a looping preview or a single finished export. Two questions total, not a full brief.

### 3. Build the HTML

Write a single self-contained HTML file following `references/composition-contract.md`
— a fixed-pixel `#stage`, a `window.__clip` object (a `gsap.timeline()` instance
satisfies this for free) with `.duration()` / `.seek(seconds)`, assets referenced by
relative path and copied next to the file. Use the project's real confirmed colors,
fonts, logo, and screenshots — never placeholder/generic branding once real brand
material exists.

`examples/starter.html` is a minimal working seed (logo-in → headline → logo-out, ~4s)
— copy and extend it rather than starting from a blank file.

### 4. Preview

```bash
open path/to/composition.html
```

Cheap and instant — iterate here first. Only move to rendering once the user is happy
with the motion and content.

### 5. Render to a real video file

One-time setup (per machine, not per video):

```bash
cd <skills>/webclip/scripts && npm install && npx playwright install chromium
```

Then, for every render:

```bash
node <skills>/webclip/scripts/render.mjs path/to/composition.html \
  --out path/to/output.mp4 \
  --width 1080 --height 1920 --fps 30
```

Flags: `--duration <seconds>` to override `window.__clip.duration()`, `--audio
<track.mp3>` to mix in a background track (requires the user's own track — this skill
doesn't generate music). See `references/ffmpeg-recipes.md` for vertical/horizontal/
square/transparent-webm/gif presets and the audio-mix recipe.

Rendering is the expensive step — don't re-run it on every small edit. Re-render only
once the previewed HTML is confirmed.

### 6. Hand off

Report the output file path, resolution, fps, and duration actually produced.
