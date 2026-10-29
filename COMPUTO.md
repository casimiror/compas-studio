# Cómputo: qué corre en cada equipo y cómo manejarlo

Compas Studio tiene que funcionar en el equipo que haya, no solo en el Mac de desarrollo. Cada script escoge su motor según
el **perfil del equipo**, sin configurar nada a mano.

## 1. Saber qué equipo es

```bash
~/.venvs/studio/bin/python -I skills/studio-edit/scripts/equipo.py
```

Escribe `~/.config/compas-studio/equipo.json` y muestra el plan. Correrlo al instalar y cada vez que cambie el equipo.
`STUDIO_DEVICE=cpu` simula un equipo sin GPU (sirve para probar los respaldos). `STUDIO_WHISPER_MODEL` cambia el modelo de transcripción.

## 2. Niveles y motores

| Paso | `mac-mlx` (Mac con Apple Silicon) | `cuda` (PC/servidor con GPU NVIDIA) | `cpu` (cualquier otro) |
|---|---|---|---|
| Transcripción (`analyze.py`) | mlx-whisper large-v3-turbo | faster-whisper large-v3-turbo, float16 | faster-whisper **small**, int8 |
| Máscaras (`mask.py`) | SAM 2.1 MLX (mejor seguimiento) o YOLO en MPS | YOLO en CUDA (SAM 2.1 MLX no corre) | YOLO en CPU; `--engine sam2` cae a YOLO solo |
| Recorte de fondo (`--engine rembg`) | BiRefNet en CPU (lento en todos) | igual | igual |
| Profundidad (`depth.py`) | Depth Anything V2 Small en MPS | CUDA | CPU (rápido: es una imagen) |
| Voz clonada (Chatterbox) | MPS | CUDA | CPU: lento, **no medido**; ver "Cómo manejarlo" |
| Separar voz/música (demucs) | MPS/CPU | CUDA | CPU (minutos por canción) |
| Render de capas y reels (`webclip`), `compose.py`, `qa.py` | Chromium + ffmpeg | igual | igual |

## 3. Tiempos medidos (2026-10-28)

Prueba con un clip de voz de 6 s y uno de 3 s a 540p. Mac M1 Pro, 32 GB. El nivel `cpu` se simuló en el mismo Mac
(`STUDIO_DEVICE=cpu`); en un portátil sin GPU será más lento.

| Paso | mac-mlx | cpu (simulado) |
|---|---|---|
| Transcribir 6 s de voz | 11 s (large-v3-turbo) | 17 s (small) |
| Máscaras de 3 s de video | YOLO 9 s · SAM 2.1 15 s | YOLO 16 s |
| Profundidad de una foto | 5 s | 4 s |
| Render de un reel de 48 s | 37 s | — (no depende de GPU) |
| Voz clonada, una frase | ~40 s | sin medir |

La primera vez que corre cada motor descarga su modelo (whisper, YOLO, Depth Anything, BiRefNet, Chatterbox): de cientos de MB
a ~1 GB cada uno. Dejar espacio y conexión la primera vez.

## 4. Cómo manejarlo

- **El director (`studio-direccion`) planea con el perfil a la vista.** Antes de prometer un efecto, mira `equipo.json`:
  - En `cpu`: preferir efectos sin máscara (texto encima, capturas, motion graphics); "texto detrás de la persona" solo en tomas
    cortas (2–4 s) y avisando el tiempo. Nada de máscaras en clips largos.
  - En `cpu`, la voz clonada no se genera ahí: se usa la voz real de la persona, o se genera en un equipo `mac-mlx`/`cuda` y se
    copia el `.wav`. Si algún día se usa un servicio de voz pago, va con aprobación del usuario.
  - En `cuda`: todo corre; la diferencia es que el seguimiento fino de un objeto es con YOLO, no con SAM 2.1.
- **Lo pesado se hace una vez:** transcribir y enmascarar se guardan en la carpeta del video (`words.json`, `masks/`) y no se
  repiten al cambiar la animación. Re-render solo cuando el usuario aprueba el preview.
- **Trabajar con clips cortos:** cortar la toma al tramo que se usa antes de enmascarar (`ffmpeg -ss … -t …`).
- **Memoria:** con 8 GB de RAM, cerrar el navegador antes de máscaras o voz clonada; un paso pesado a la vez.
- **Si algo no corre en el equipo**, el script lo dice y usa el respaldo (por ejemplo SAM 2.1 → YOLO). Nunca se cambia el plan
  en silencio: el director le dice al usuario qué efecto cambió y por qué.

## 5. Decírselo a quien lo usa y darle alternativas

Al empezar con un equipo nuevo, y cada vez que un paso no corra o vaya a tardar mucho, **se le dice al usuario en una línea**
qué no puede hacer este equipo y se le dan opciones (las imprime `equipo.py`). Nunca se cambia un efecto en silencio.

| Si no se puede… | Sin servicios externos | Con servicios externos (cuenta y llave del usuario; casi todos cobran) |
|---|---|---|
| Voz clonada | Grabar la frase con la voz real; o generar el `.wav` en un equipo `mac-mlx`/`cuda` y copiarlo | **ElevenLabs** (clona la voz), **Resemble AI** (los de Chatterbox); voz sin clonar: OpenAI TTS, Google Cloud TTS, Azure Speech |
| Transcripción rápida | faster-whisper `small` en CPU (incluido) | OpenAI (Whisper / gpt-4o-transcribe), Deepgram, AssemblyAI, Groq; o los subtítulos automáticos de CapCut / Instagram |
| Máscaras (texto detrás de la persona) | Texto encima; YOLO en CPU sobre 2–4 s | SAM 2 alojado en Replicate o fal.ai; quitar fondo en CapCut o Runway |
| Un lote pesado | Dejarlo corriendo de noche | Alquilar GPU por horas: Google Colab, RunPod, Modal |

Reglas para los servicios externos:
- **Solo con aprobación del usuario** y en su cuenta. Las llaves (`ELEVENLABS_API_KEY`, etc.) las pone él en su entorno; el agente
  nunca escribe ni pide contraseñas o llaves en el chat.
- Antes de usar uno, decir qué se le envía (audio, video, la voz de alguien) y que puede costar. Precios y planes cambian: revisarlos en la página del servicio.
- Clonar una voz solo con permiso de su dueño.
- Lo que salga de un servicio se marca en el storyboard (`gen-*`), igual que lo generado localmente.

## 6. Instalar por nivel

Comunes a todos: `ffmpeg`, Node 20+ (`cd skills/webclip/scripts && npm install && npx playwright install chromium`),
Python 3.11 en `~/.venvs/studio` con: `torch`, `ultralytics`, `scenedetect`, `librosa`, `rembg`, `transformers`,
`opentimelineio`, `opencv-python`, `faster-whisper`.

| Nivel | Además |
|---|---|
| mac-mlx | `mlx-whisper` en `~/.venvs/studio`; `~/.venvs/sam-mlx` (Python 3.14 + `mlx-sam`); Chatterbox en `~/.venvs/chatterbox` |
| cuda | `torch` con CUDA; Chatterbox en `~/.venvs/chatterbox` con CUDA |
| cpu | nada más (sin SAM 2.1; voz clonada desde otro equipo) |

Pesos de YOLO en `~/.cache/studio-models/` (`yolo11m-seg.pt`, `yolo11m.pt`).
