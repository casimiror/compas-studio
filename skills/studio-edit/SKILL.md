---
name: studio-edit
description: >
  Edita video real mezclándolo con motion graphics en JS: cortes, reencuadre vertical, zoom, color y transiciones
  con ffmpeg; transcript palabra a palabra (mlx-whisper); segmentación y seguimiento del sujeto (YOLO-seg, SAM 2.1,
  BiRefNet, MatAnyone 2 para recorte de precisión) para poner texto DETRÁS de la persona o etiquetas que la siguen;
  profundidad para parallax 2.5D; transformar a la persona en otro estilo (anime, cómic, videojuego…: imagen de Gemini +
  transición + parallax); capas
  HTML/GSAP con alfa renderizadas con webclip; mezcla de voz, música con ducking y volumen a -14 LUFS; QA con hojas de
  contacto; exporta la línea de tiempo a OTIO (FilmCraft, Resolve, Kdenlive). Úsala cuando haya material grabado que
  editar, "texto detrás de la persona", subtítulos animados, "que el texto siga al producto", reencuadrar horizontal a
  vertical, o cuando el agente compas-studio produzca un video.
---

# studio-edit

> `<skills>` es la carpeta donde quedaron instaladas las skills (por ejemplo `~/.claude/skills` o `.claude/skills` del proyecto). Las skills de Compas Studio se instalan juntas, así que una puede usar los scripts de otra.

**La idea:** nunca se le pide todo a un solo motor. Cada capa la hace la herramienta que mejor la hace, se revisa por
separado, y ffmpeg las apila al final. Un error en una capa se arregla rehaciendo solo esa capa.

```
material real ──compose --stage base──▶ base.mp4 ──analyze──▶ words.json, escenas, beats
                                           │──mask──▶ subject.mov (alfa) + track.json
                                           ▼
             behind.html ─render.mjs --transparent─▶ behind.webm ┐
             front.html  ─render.mjs --transparent─▶ front.webm  ├─compose --stage final─▶ final.mp4 ─qa─▶ entregar
             voz (Chatterbox), música, sfx ──────────────────────┘                     └─▶ timeline.otio
```

Orden de capas de abajo arriba: **base → behind (texto grande, formas) → subject (el sujeto recortado) → front (subtítulos, etiquetas, CTA)**.
Con eso la persona queda delante del texto, que es el efecto que hace que no parezca una plantilla.

## Cuenta

`render.mjs` usa Chromium: no correrlo donde una regla del usuario (`CLAUDE.md`, hooks) prohíba navegadores.

## Entorno

**Primero el equipo:** `~/.venvs/studio/bin/python -I scripts/equipo.py` dice el nivel (`mac-mlx`, `cuda` o `cpu`) y qué motor usa
cada paso; los scripts lo leen solos (transcripción con mlx-whisper o faster-whisper, SAM 2.1 solo en Mac con Apple Silicon y si no
YOLO, torch en MPS, CUDA o CPU). Qué corre en cada nivel, tiempos y cómo planear con poco cómputo: `COMPUTO.md` en la raíz del producto.


- SAM 2.1: `~/.venvs/sam-mlx` (Python 3.14 + `mlx-sam`, sin PyTorch). Pesos de YOLO en `~/.cache/studio-models/`.
- MatAnyone 2: `~/.venvs/matanyone` (Python 3.12, torch con MPS), código en `~/.venvs/matanyone2-src`. Lo llama `matting.py`.
- Python: `~/.venvs/studio` (3.11, torch con MPS, ultralytics, scenedetect, librosa, mlx-whisper, rembg, transformers, opentimelineio).
  Siempre `~/.venvs/studio/bin/python -I <script>`.
- Voz: Chatterbox en `~/.venvs/chatterbox` (la voz de referencia de cada proyecto está en su `brand.md`).
- Render de capas: `node <skills>/webclip/scripts/render.mjs <capa.html> --out <capa.webm> --transparent [--duration S]`.
- Scripts en `<skills>/studio-edit/scripts/`; plantillas en `templates/`.

## Scripts

| Script | Qué hace | Tiempo aprox. (M1 Pro) |
|---|---|---|
| `analyze.py <video> <dir> [--beats] [--no-words]` | metadatos, escenas, `words.json` (whisper large-v3-turbo, español), beats, `contact.jpg` | ~5 s + 1 s por cada 10 s de voz |
| `mask.py <video> <dir> [--engine yolo\|sam2\|rembg]` | `masks/`, `subject.mov` (ProRes 4444 con alfa), `track.json` | yolo ~4 s por segundo de video; sam2 ~5 s por segundo (MLX a 512); rembg ~30 s por segundo |
| `matting.py <video> <dir> [--mask m.png] [--max-size N]` | recorte de precisión con MatAnyone 2: `alpha.mp4`, `subject.mov` (alfa suave) | ~1,4 s por frame a 1080p (3 s ≈ 2 min 20 s) |
| `depth.py <img> <depth.png>` | mapa de profundidad (Depth Anything V2) para parallax | segundos |
| `estilo_parallax.py <img> <mask> <bg> <out.mp4> [seg]` | anima una imagen fija en 2.5D: sujeto y fondo en capas, halo que palpita, líneas de velocidad, partículas, flash y temblor | segundos |
| `pack.py <data.js> --words --track --extra [--offset]` | datos para las plantillas (`window.STUDIO`) | — |
| `compose.py edit.json --stage base\|final --out X [--otio Y] [--dry]` | arma el video (formato en `references/edit-spec.md`) | ~2× tiempo real |
| `qa.py <video> <dir> --ig` | medidas, LUFS, pico, negros, congelados, silencio inicial, `sheet.jpg` con zonas seguras, frame0/mid/last | segundos |

Motores de `mask.py`:
- `yolo` (por defecto): personas (`--classes 0`) u objetos COCO (39 botella, 41 taza, 24 morral, 26 bolso, 32 balón…). Rápido; buen borde.
- `sam2`: SAM 2.1 en MLX (`mlx-sam`, entorno `~/.venvs/sam-mlx` con Python 3.14, lo llama `sam_mlx.py`). El mejor seguimiento:
  no salta a otra persona y suelta al sujeto cuando sale de cuadro. Prompt: sin nada, YOLO pone la caja del objeto más grande de `--classes`
  en `--frame`; o `--box x0,y0,x1,y1`; o `--point x,y` (un clic suelto es ambiguo: puede tomar solo la oreja). `--frame N` propaga a ambos lados.
  `--size 512` (por defecto, ~0,1 s/frame) da casi el mismo borde que 1024 (~0,65 s/frame); la máscara sale siempre en la resolución del video.
  Es la opción para producto (tarro, tenis) y para personas cuando hay más gente en cuadro.
- `rembg --rembg-model birefnet-portrait|birefnet-general`: el mejor borde (pelo, producto), el más lento. Para tomas cortas y planos detalle.
  También es el que recorta personas **dibujadas** (ilustraciones generadas con Gemini): YOLO no las detecta.

**YOLO es el motor principal** (rápido y suficiente casi siempre). **MatAnyone 2 (`matting.py`) solo cuando haga falta precisión**:
cambiar el fondo completo, planos cerrados, cuando el halo de YOLO se nota (YOLO deja un borde oscuro alrededor del cuerpo y
recortes imperfectos con mancuernas). MatAnyone 2 da alfa suave de video entero, pero solo recorta personas: un objeto en la mano
(mancuerna, producto) queda fuera salvo que la `--mask` del primer frame lo incluya (hazla con `mask.py --engine sam2`).

**ViBT / Vision Bridge (estilizar o colorear el video entero con Wan 2.1): no usar en Mac ni en equipos sin NVIDIA.** En Apple Silicon
(M1 Pro) tarda más de 10 min solo en codificar 2 s, pesa unos 40 GB y trae CUDA fijo en el código. Solo se usa si el equipo tiene GPU
NVIDIA con VRAM de sobra (`equipo.py` en nivel `cuda`) o un servicio en la nube que lo ofrezca.

## Transformar a la persona en otro estilo

El estilo lo elige el usuario (anime, cómic, videojuego, pintura, plastilina…); aquí está la técnica, igual para todos.

1. **La imagen:** un frame del video (`ffmpeg -ss T -frames:v 1`) se sube a Gemini (flujo en el agente `compas-studio`) con el
   prompt: "redibuja esta foto exacta en estilo <estilo elegido>, MISMA pose, MISMO encuadre 9:16, mismos rasgos, ropa y objetos;
   fondo en el mismo estilo; <efecto opcional: aura, brillo…>; sin texto". Gemini conserva la pose casi idéntica, así que el corte
   real → ilustración coincide cuadro a cuadro. Si alguien sale cerca en el frame, pide que lo quite.
2. **La transición** (ffmpeg o capa JS):
   - barrido de escaneo: `xfade=wipedown` de 0,6 s + una línea de luz con `drawbox` que baja con `t` (por donde pasa ya es ilustración);
   - cruce de texto: una palabra pasa delante del sujeto y al salir ya es ilustración (encaja si la pieza ya usa texto detrás del sujeto);
   - flash blanco: corta a la ilustración en el blanco.
3. **El movimiento:**
   - `estilo_parallax.py` (local, gratis): recorta el dibujo con `rembg` BiRefNet, rellena el fondo con `cv2.inpaint` y lo anima.
     **Es un efecto de acento, no la transformación potente**: la persona no se mueve, solo la cámara y los efectos. Úsalo en 1–3 s. Con zoom fuerte un brazo estirado se sale de cuadro: baja el zoom.
   - Movimiento real (que la persona de verdad se mueva o se transforme): image-to-video generado. Ver
     "Generar lo que no se grabó" en `compas-studio` (Veo en Gemini por defecto; servicios de pago solo si el usuario los aprobó).

## Plantillas (`templates/`)

Copia `studio.js` y las que uses a la carpeta del video, junto a `data.js`. Cumplen el contrato de webclip (`window.__clip`).
- `behind.html`: titular gigante que entra desde grande (visible en el frame 0) y se ajusta solo al ancho. Va detrás del sujeto.
  El sujeto tapa parte del texto, y eso es el efecto, pero cada palabra tiene que seguir leyéndose: mira `track.json`
  (dónde está la cabeza) y pon las líneas por encima o al lado. Si el sujeto tapa más de un tercio de una palabra, muévela.
  El tamaño se calcula antes de armar la animación: si se cambia después, el texto salta (bug del 2026-10-26).
- `front.html`: subtítulos palabra a palabra (la palabra que suena en neón) + etiqueta que sigue la cabeza del sujeto
  (`extra.json`: `{"duration": D, "tag": {"text": "@tienda", "from": 0.6, "to": 3.6}, "maxWords": 3}`). Respeta las zonas seguras.
- `STUDIO.trackAt(t)`, `STUDIO.chunks(n)`, `STUDIO.smoothTrack(w)` y `STUDIO.exportClip(tl, onSeek)` sirven para escribir capas nuevas:
  cualquier cosa que dependa del sujeto (flechas, círculos, precios que lo siguen, zoom a una zona) se dibuja en `onSeek`.
- Los colores y las fuentes son variables CSS en `:root`: cámbialos por los del `brand.md` del proyecto.

Para capas más complejas (Three.js, shaders, Lottie, mapas) escribe el HTML con las skills de `hyperframes-animation`
o `hyperframes-registry` como referencia de técnica, pero entrégalo como capa transparente de webclip: la composición siempre la cierra `compose.py`.

## Cuándo usar otra cosa

- **HyperFrames** (`/hyperframes`): piezas 100 % motion sin material grabado, o cuando el usuario quiera abrir y editar el proyecto en HyperFrames Studio.
- **FilmCraft** (editor libre, alfa, instalado 2026-10-26): la mesa de **retoques finales dirigidos por el usuario**.
  1. `compose.py edit.json --stage final --out final.mp4 --otio final.otio` (en etapa final el V1 del .otio es el base con color,
     las capas van encima y el audio queda por roles).
  2. `python3 -I scripts/fc_finish.py edit.json final.otio fc/<nombre>.fcproj`: importa, pone tamaño y fps, aplica volúmenes y recentra.
  3. `filmcraft-open fc/<nombre>.fcproj` abre la app con el canal de control (token nuevo por sesión en `~/.config/filmcraft/`).
  4. MCP `filmcraft` (puente, la app abierta) o `filmcraft-headless` (sin ventana). Ciclo: `sequence_inspect` → `command_run` →
     `render_frame` o `ui_screenshot` → mostrar al usuario → `edit.undo` si no le gusta. CLI equivalente: `filmcraft-cli --bridge 127.0.0.1:9876`.
  5. Exportar: `file.exportMedia` con `format: h264`, `loudnessLufs: -14`. Revisar con `qa.py` igual que siempre.
  No viaja en el .otio: el `vf` de las capas (la luz de relleno del sujeto) ni los filtros de audio; se rehacen en FilmCraft si hacen falta.
- **Resolve / Kdenlive**: el usuario abre el `.otio` para terminar a mano.

## Look por defecto

Para material de exteriores, arranca con el "dorado" del reel fondo-16k (en `references/edit-spec.md`: `vf` de curvas suaves,
temperatura 5300 K al 45 %, vibrance 0,18 y viñeta) y la luz de relleno sobre `subject.mov`. Al usuario le gustó más que
el material sin tratar (2026-10-26). Baja la viñeta en tomas con el horizonte o el sol en cuadro.

## QA (obligatorio antes de entregar)

1. `qa.py final.mp4 qa --ig` y lee `qa.json`: sin warnings, o cada warning explicado.
2. Mira con Read `qa/sheet.jpg`, `qa/frame0.png` y `qa/mid.png`. Revisa: el hook se lee en el frame 0; nada importante en las franjas rojas;
   el borde de la máscara no deja halos ni recorta pelo o manos; los subtítulos coinciden con lo que se oye; no hay texto cortado.
3. Si una capa falla, rehaz solo esa capa y vuelve a correr `--stage final` (segundos).
4. Si no se pudo medir algo (falta una herramienta, un render falló), entrégalo como **pendiente**, no como listo.
