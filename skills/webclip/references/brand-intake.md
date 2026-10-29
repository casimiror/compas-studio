# Brand intake — assisted, not silent, not a full interview

> `<skills>` is the folder where the skills are installed (e.g. `~/.claude/skills` or the project's `.claude/skills`). Compas Studio skills are installed together, so one can call another's scripts.

`scripts/probe-brand.mjs` does a best-effort scan of the current project. Run it from
the project root before writing any composition:

```bash
node <skills>/webclip/scripts/probe-brand.mjs
```

It looks for, in order:

1. **Style guide / design-token docs** — any `docs/**/*.md` whose filename mentions
   "style guide" or "design tokens/system", plus `CLAUDE.md` at the project root. It
   pulls out hex colors (`#RRGGBB`) and `font-family` names it can find via regex — a
   rough pass, not a real parser, so double check anything that looks off before using
   it (e.g. a color pulled from an unrelated code sample).
2. **Logo** — files matching `*logo*.{png,svg,webp,jpg,jpeg}` under common asset dirs
   (`assets/logo`, `public/logo`, `src/assets/logo`, `branding`, `assets/brand`), with a
   shallow fallback search under `assets/`, `public/`, `src/` if nothing turns up there.
3. **Screenshots / product shots** — file listing (names only, no analysis) from common
   screenshot/image directories.

It prints one JSON object and always exits 0, even on an empty project
(`confidence: "empty-scan"` in that case) — never treat a failed/empty scan as a hard
error, just tell the user nothing was found and ask for paths directly.

## Presenting the results

Don't build anything from the scan silently, and don't turn this into a multi-question
interview either — **one confirmation round**:

> Found: colors `#3DD598`, `#FF8A65`, `#5B9BF3`... / fonts `Poppins`, `Inter` / logo at
> `assets/logo/compas_logo.png` / screenshots: `captain_dashboard.png`,
> `panel_de suscripciones.png`, ... — ¿uso estos, cambio alguno, o agrego algo más?

If a relevant screenshot exists in a demo/example sub-brand with its *own* distinct
visual identity (different colors, different tone — e.g. a sample storefront built on
top of the platform, not the platform's own primary brand), say so explicitly and ask
whether that's acceptable as "an example of what you can build" or whether a different,
on-brand asset should be used instead. Don't silently present a sub-brand's styling as
if it were the primary brand's.

## When nothing useful is found

If `confidence` is `"empty-scan"` or the hits look thin, ask the user directly for:
- 2–4 hex colors (or "just use something sensible/neutral")
- a font name or two (or accept a safe default pairing, e.g. a bold geometric sans for
  headlines + a clean sans for body)
- a logo file path, if one exists
- any screenshots/photos worth including

## Generating what doesn't exist

`webclip` does not generate images itself. If a scene needs something that isn't in the
project and isn't a simple color/shape/text treatment:

- **Logo, icon, banner** → suggest `/design` (Gemini-based generation, multiple styles)
- **Any other image/photo, or a resolve-first lookup before generating** → suggest
  `/media-use`
- **A templated graphic or branded layout** → suggest the Canva connector
  (`mcp__claude_ai_Canva__*`, already available in this environment — needs sign-in via
  its `authenticate` tool on first use)
- **Design tokens/components/exported frames from an existing Figma file** → suggest
  `/figma`

Whatever comes back from any of those is just another confirmed asset — copy it next to
the composition HTML and reference it by relative path like the logo or a screenshot.
`webclip` never talks to these tools directly; it only tells the user when one of them
would help and treats the output the same way either way.
