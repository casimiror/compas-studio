# ffmpeg recipes

`render.mjs` already picks a sensible default per `--format`/extension (see below), but
here's what it's doing and how to override it for less common cases.

## Resolution / aspect presets (pass via `--width`/`--height`)

| Use case | Width x Height |
| --- | --- |
| Reel/Story/TikTok/WhatsApp status | `1080x1920` |
| Horizontal / web / YouTube | `1920x1080` |
| Square (feed post) | `1080x1080` |

## Format defaults `render.mjs` applies

- **`.mp4` (default)** → `ffmpeg -framerate <fps> -i frame_%05d.png -c:v libx264 -pix_fmt yuv420p -crf 18 out.mp4`
  `crf 18` is visually near-lossless; raise to `20-23` for smaller files if quality loss
  is acceptable.
- **`.gif`** → `-vf fps=<fps>,scale=<width>:-1:flags=lanczos out.gif`. GIFs get large
  fast — keep these short (a few seconds) and consider trimming `--fps` to 15-20.
- **`.webm` with `--transparent`** → `-c:v libvpx-vp9 -pix_fmt yuva420p -crf 30 -b:v 0
  out.webm`. Use this for an overlay that needs to sit on top of other footage (e.g. a
  logo sting composited later) — requires the composition's own background to actually
  be transparent (`background: transparent` on `#stage`, no opaque fill), not just the
  encode flag.
- **`.webm` opaque** → same as above without `yuva420p`/`omitBackground`.

## Background audio

`--audio track.mp3` adds `-i track.mp3 -shortest -c:a aac` to the ffmpeg call so the
output stops at whichever is shorter (the video or the track) — trim/loop the audio
file yourself first if it needs to match the clip exactly. This skill doesn't generate
or source music; bring your own track or get one via `/media-use`.

## Forward note: compositing a future AI-generated video clip

If/when an AI video-generation tool becomes available and authorized for use, it slots
into this same ffmpeg step rather than requiring any change to how compositions are
built:
- **As a background plate under the HTML overlay** — render the webclip composition as
  a transparent webm (above), then `ffmpeg -i background.mp4 -i overlay.webm -filter_complex overlay -c:v libx264 out.mp4`.
- **As a segment before/after the HTML-rendered clip** — encode both to the same
  resolution/fps and `ffmpeg -f concat -i list.txt -c copy out.mp4` (requires matching
  codecs, or re-encode both first).

Nothing here is built yet — this is just where it would attach.
