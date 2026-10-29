# Compas Studio

Agencia de contenido en video hecha con agentes de Claude Code: entiende qué necesita la empresa de su publicidad, decide qué
publicar, dirige la producción, edita y mide si lo publicado sirve. Compas (@compascol) es el primer cliente; la idea es que sea
un producto propio, para cualquier empresa.

## Brief

- **Problema:** las empresas pequeñas no tienen quien les diga qué publicar, lo produzca bien y mida si les trae negocio.
  Las herramientas "fancy" hacen videos bonitos que no sirven.
- **Qué hace:** de punta a punta: estrategia de redes → dirección del proyecto (series, grabaciones, orden de salida) →
  concepto y guion → edición (video real + motion graphics en JS, voz clonada, subtítulos) → métricas y aprendizajes que
  hacen evolucionar las reglas.
- **Cómo se valida:** con Compas. Si los reels traen DMs de tiendas y crecen en alcance a no seguidores, se ofrece a otras empresas.

## Piezas (jerarquía: la de arriba manda)

| Pieza | Archivo | Rol |
|---|---|---|
| Agente | `agents/compas-studio.md` | Director, diseñador de motion y editor; carga las skills en este orden |
| `studio-estratega` | `skills/studio-estratega/` | **Manda sobre todo.** Qué necesita la empresa, cómo funcionan las redes, filtro antes de producir, métricas y `aprendizajes.md` (evoluciona con datos) |
| `studio-direccion` | `skills/studio-direccion/` | Dirige la producción: tablero, sesiones de grabación, material recibido, orden de salida, cuándo usar cada herramienta |
| `studio-concept` | `skills/studio-concept/` | 2–3 conceptos desde el material, con recomendación |
| `reel-craft` | `skills/reel-craft/` | Oficio de video corto: hook, retención, chequeo antes de publicar |
| `analizar-video` | `skills/analizar-video/` | Desarma un video referente y saca la fórmula; outliers con vidIQ |
| `studio-edit` | `skills/studio-edit/` | Edición: cortes, máscaras, capas JS, voz, mezcla, QA, `.otio` |
| `webclip` | `skills/webclip/` | Motion graphics en HTML + GSAP, render a MP4 |

Datos de cada empresa (estrategia, métricas, aprendizajes, tablero, series) viven **fuera del repo**, en su carpeta de
marketing; `~/.config/compas-studio/proyectos.md` dice dónde está la de cada empresa.

## Cómputo

Funciona en Mac con Apple Silicon, PC con GPU NVIDIA o cualquier equipo solo con CPU; cada script escoge su motor según el
equipo (`skills/studio-edit/scripts/equipo.py`). Qué corre dónde, tiempos medidos y cómo planear con poco cómputo: [`COMPUTO.md`](COMPUTO.md).

## Instalar

**Todo, con el agente** (plugin de Claude Code):

```bash
/plugin install compas-studio --marketplace casimiror/compas-studio
```

o en dos pasos: `/plugin marketplace add casimiror/compas-studio` y `/plugin install compas-studio@compas-studio`.

**Solo las skills**, en Claude Code o en cualquier agente compatible (Codex, Cursor, OpenCode…), con la CLI de [skills](https://github.com/vercel-labs/skills):

```bash
npx skills add casimiror/compas-studio            # elige skills y agente
npx skills add casimiror/compas-studio --all -g   # todas, para todos tus proyectos
npx skills add casimiror/compas-studio --list     # ver qué trae
```

Instala las siete juntas: unas usan los scripts de otras (`<skills>/webclip/scripts/render.mjs`).

**Después de instalar:**

```bash
cd <skills>/webclip/scripts && npm install && npx playwright install chromium
python3 -I <skills>/studio-edit/scripts/equipo.py   # nivel del equipo y qué falta instalar
```

`<skills>` es donde quedaron las skills (`~/.claude/skills`, `.claude/skills`, `.agents/skills`…). Qué instalar según el equipo
(Mac con Apple Silicon, GPU NVIDIA o solo CPU) y las alternativas si algo no corre: [`COMPUTO.md`](COMPUTO.md).

Cada empresa necesita su carpeta de marketing (fuera del repo) registrada en `~/.config/compas-studio/proyectos.md`:

```markdown
| Empresa | Carpeta de marketing | Skills propias | Notas |
|---|---|---|---|
| Mi Marca | `~/marcas/mi-marca/marketing/` | — | — |
```

## Licencia

MIT. Ver [`LICENSE`](LICENSE).
