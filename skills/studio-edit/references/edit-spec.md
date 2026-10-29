# edit.json: el formato del montaje

Un solo archivo describe el video. `compose.py` lo convierte en comandos de ffmpeg; `--otio` lo exporta como
línea de tiempo para abrirlo en FilmCraft, DaVinci Resolve o Kdenlive. Rutas relativas al edit.json.

```jsonc
{
  "name": "proteina-quilla",
  "size": [1080, 1920], "fps": 30,

  // Etapa base: cortes sobre el material real. Los tiempos x/y/zoom son segundos desde el inicio del clip ya cortado.
  "clips": [
    {"src": "media/tienda.mov", "in": 2.4, "out": 5.1,
     "fit": "cover",                      // cover (llena y recorta) | blur (horizontal dentro de vertical, fondo desenfocado)
     "zoom": [[0, 1.0], [2.7, 1.12]],     // punch-in lento; 1 = cover justo
     "x": [[0, 0.45], [2.7, 0.55]],       // centro del encuadre (0-1 del ancho escalado): reencuadre/paneo
     "y": [[0, 0.5]],
     "speed": 1,                          // 0.5 = cámara lenta (mejor si el material es de 60 fps)
     "audio": true, "gain": -6,           // sonido directo del clip
     "lut": "luts/calido.cube", "eq": "contrast=1.08:saturation=1.15",
     "vf": "curves=all='0/0.03 0.25/0.26 0.5/0.53 0.8/0.83 1/0.97',colortemperature=temperature=5300:mix=0.45,vibrance=intensity=0.18,vignette=angle=PI/5",
                                          // vf = cualquier filtro de ffmpeg; este es el "dorado" del reel fondo-16k
     "transition": {"type": "fade", "dur": 0.25}   // con el clip ANTERIOR. Tipos de xfade: fade, smoothup, slideleft,
                                                   // circleopen, zoomin, wipeleft, dissolve, hblur, fadeblack…
    }
  ],

  // Etapa final: base + capas con alfa en orden (la primera queda más abajo) + audio.
  "base": "out/base.mp4",
  "layers": [
    {"src": "out/behind.webm", "start": 0},          // motion DETRÁS del sujeto
    {"src": "out/mask/subject.mov", "start": 0,      // el sujeto recortado (mask.py) lo tapa
     "vf": "eq=gamma=1.12:brightness=0.02:saturation=1.06"},  // luz de relleno SOLO sobre el sujeto
    {"src": "out/front.webm", "start": 0, "opacity": 1}  // subtítulos, etiquetas, CTA
  ],
  "base_audio": true, "base_gain": 0,
  "audio": [
    {"src": "voz/voz.wav", "start": 0.2, "role": "voice"},
    {"src": "musica/beat.mp3", "start": 0, "gain": -14, "role": "music", "trim": [12, 40], "fade_out": 0.8},
    {"src": "sfx/whoosh.wav", "start": 2.7, "gain": -6, "role": "sfx"}
  ],
  "duck": true,          // la música baja sola cuando habla la voz (sidechain)
  "loudness": -14        // LUFS integrados de salida (Instagram/TikTok normalizan cerca de -14)
}
```

## Reglas

- **El sujeto se segmenta sobre `base.mp4`, no sobre el material original**: así máscara, track y capas comparten
  el mismo reloj. Orden: `--stage base` → `analyze.py` + `mask.py` sobre base → capas HTML → `--stage final`.
- Una capa que empieza después del segundo 0 lleva `start`; su HTML cuenta el tiempo desde 0, y `pack.py --offset`
  desplaza words/track para que coincidan.
- Las capas `.webm` necesitan alfa real: render con `render.mjs --transparent` y extensión `.webm`.
- `transition` acorta el total en `dur` segundos (los clips se solapan). `compose.py` imprime la duración final.
- Para ver el comando sin correrlo: `--dry`.

- **Corrección de color y re-iluminación:** el color va en `vf` de cada clip (etapa base). Para que el sujeto se separe del fondo,
  aclara solo la capa `subject.mov` con `vf`. Si cambias el color de la base, rehaz `subject.mov` sobre la base nueva (las
  máscaras se reusan): `ffmpeg -i base.mp4 -framerate 30 -i mask/masks/%05d.png -filter_complex "[1:v]format=gray,gblur=sigma=1.5[m];[0:v][m]alphamerge,format=yuva444p10le" -c:v prores_ks -profile:v 4444 mask/subject.mov`.
