# The webclip composition contract

A webclip composition is a single HTML file plus its relative assets — no build step,
no HyperFrames runtime, no `data-*` timing attributes. `render.mjs` only needs three
things from the page.

## 1. A fixed-pixel stage

Pick the target resolution up front and size the root element to match exactly (e.g.
`1080x1920` for a vertical reel, `1920x1080` horizontal, `1080x1080` square). Don't rely
on viewport-relative units for the stage itself — `render.mjs` sets the Playwright
viewport to this exact size, so pixel values are safe and predictable.

```css
#stage { position: relative; width: 1080px; height: 1920px; overflow: hidden; }
```

## 2. `window.__clip` — the seek contract, and why `.seek()`'s return value matters

> **The single biggest render-speed/reliability issue found building this skill** was
> not a timing race — it was `render.mjs` calling
> `page.evaluate((t) => window.__clip.seek(t), t)`. An arrow function with an
> expression body returns whatever that expression evaluates to, and GSAP's `.seek()`
> returns the timeline itself (for chaining) — a large object full of circular
> references. Playwright then has to serialize that whole object back to Node on
> **every single captured frame**. This is slow in proportion to how big/complex the
> timeline is (it's the real reason a simple 4-scene logo clip captured at ~2 fps while
> a dense multi-screenshot composition dropped to ~0.5 fps) and, confirmed while
> debugging this, occasionally hangs outright. `render.mjs` now calls `.seek()` inside
> a block body (`(t) => { window.__clip.seek(t); }`) so nothing is returned — if you
> ever touch that call, keep it that way.

`render.mjs` drives the animation by calling `window.__clip.seek(t)` for every frame

`render.mjs` drives the animation by calling `window.__clip.seek(t)` for every frame
(deterministic capture, not real-time recording) and reads `window.__clip.duration()`
once up front. The object must expose:

- `duration()` → number of seconds in **one finite cycle**. Never infinite.
- `seek(seconds)` → synchronously jump the whole composition to that time. No reliance
  on `requestAnimationFrame` continuing to run between calls.

A GSAP timeline already satisfies this shape — a `gsap.timeline()` instance has both
`.duration()` and `.seek(time)` methods built in. Just don't use `repeat: -1` on the
timeline you assign to `window.__clip` (infinite repeat has no finite `.duration()` to
export cleanly).

### Never `.play()` or `.restart()` the exported timeline — ever, not even for preview

This is the single most important rule in this contract. `render.mjs` drives
`window.__clip` purely by calling `.seek(t)` over and over; it never plays it. If
*anything else* also calls `.play()`/`.restart()` on that same object — including a
"just for browser preview, looks harmless" auto-loop — it hands the timeline to GSAP's
ticker, which keeps advancing it in real time on every `requestAnimationFrame`,
**concurrently** with `render.mjs`'s manual seeks. The two drivers race for every
captured frame. On a slow capture (minutes of wall-clock time to capture a few seconds
of timeline) the live ticker wins almost every time, and the rendered output comes out
flickering / stuck on whatever the live loop last drew instead of the requested frame
— this exact bug showed up rendering the Compas acceptance clip (it looped on the logo
scene the whole way through). **There is no reliable way for `render.mjs` to stop this
from its side once it's started** — `gsap.ticker.sleep()` looks like it should pause
an active timeline but, confirmed by isolated testing, does not: a timeline already
mid-`.play()` kept auto-restarting with the ticker "asleep." The only fix is to never
start the ticker on this object in the first place.

### Looping for human preview — drive it the same way `render.mjs` does

If you want the composition to auto-loop when opened directly in a browser, drive that
loop with your own `requestAnimationFrame` calling `.seek()` — the same mechanism
`render.mjs` uses — and have it check `window.__renderMode` every tick so it gets out
of the way the instant a real render starts (`render.mjs` sets this flag right after
the page is confirmed ready, before any capturing begins):

```js
const tl = gsap.timeline({ paused: true }); // never played — this is what gets exported
// ...build the timeline...
window.__clip = tl;

// Preview-only loop. Uses .seek(), never .play()/.restart() — tl.isActive() stays
// false forever as far as GSAP's ticker is concerned, so there is nothing for
// render.mjs's own seeks to race against.
(function previewLoop(startTime) {
  if (window.__renderMode) return; // render.mjs has taken over — stop ticking
  const elapsed = (performance.now() - startTime) / 1000 % tl.duration();
  tl.seek(elapsed);
  requestAnimationFrame(() => previewLoop(startTime));
})(performance.now());
```

Implement the same two methods (`duration()`/`seek()`) manually for a non-GSAP
composition — e.g. toggle classes / set inline styles based on the seconds passed in —
with no transition duration needed since `render.mjs` never watches a transition
finish, only the state after `seek()` returns. The same rule applies: whatever drives
your own preview loop must be seek-based and must check `window.__renderMode`, never a
`play()`/timer-based animation running independently of it.

## 3. Assets stay relative, fonts stay gated

- Reference every image/logo/screenshot by a **relative path** next to the HTML
  (`assets/logo.png`, not `file:///Users/...`). `render.mjs` serves the HTML's directory
  over a local `http://127.0.0.1` server specifically so relative paths and web fonts
  load the same way a real browser would — `file://` pages have CORS/font-loading
  quirks that make seek-capture unreliable.
- If using web fonts (Google Fonts or self-hosted), nothing extra is required — the
  render script already waits on `document.fonts.ready` before capturing frame 0. Just
  don't start any animation before that point in your own preview code either, or the
  preview will show a flash of fallback-font text that the render never does.

## Checklist before rendering

- [ ] `#stage` (or equivalent root) is exactly the target pixel size
- [ ] `window.__clip` is assigned, finite, has working `.duration()` / `.seek()`
- [ ] All asset/font paths are relative, resolvable from the HTML's own directory
- [ ] Opened the file directly in a browser and the motion looks right before rendering
