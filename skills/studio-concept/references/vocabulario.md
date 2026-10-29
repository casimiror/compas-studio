# Vocabulario de hooks, cámara, luz y sonido

Adaptado de las skills de [rediumvex/ai-video-generator-claude](https://github.com/rediumvex/ai-video-generator-claude) (MIT),
escritas para prompts de Seedance. Aquí cada recurso dice cómo se logra: **[edit]** con studio-edit sobre material real,
**[veo]** pidiéndolo a Veo en Gemini, **[grabar]** pidiéndole la toma al usuario, **[nuevo]** si todavía no existe.
Sus cifras de alcance ("80 % de finalización = 2–3× alcance") no tienen fuente: no se citan.

## Patrones de hook (frame 0 a 2 s)

| Patrón | Qué hace | Cómo |
|---|---|---|
| Dato detrás del sujeto | El número gigante y la persona delante | [edit] máscara + `behind.html` |
| Reacción antes que la causa | Cara de sorpresa o esfuerzo; la causa llega después | [grabar] o [edit] eligiendo la toma |
| Sujeto escondido | Detalle (manos, zapatillas, reloj) sin mostrar todo; se revela a los 2 s | [edit] punch-in fuerte que abre con `zoom` |
| Antes y después en 0,8 s | Corte o wipe entre dos estados | [edit] `xfade` (wipeleft, slideup) + sfx |
| Tipografía cinética | 3–5 palabras que golpean al beat, micro-sacudida | [edit] capa HTML (GSAP) + `--beats` |
| Silencio y golpe | 1–1,5 s casi en silencio y luego bajo + corte | [edit] `audio` con `start` + sfx |
| Color que explota | Arranca desaturado y un elemento se enciende | [edit] `eq=saturation` por clip; por tramos es [nuevo] (keyframes de color) |
| Movimiento repentino | Plano quieto 1 s y algo entra rápido | [grabar] o [veo] |
| Contacto visual | Ojos a cámara en el frame 0 | [grabar]: la toma de frente |
| Cuenta regresiva | 3-2-1 con un golpe en cada número | [edit] capa HTML |
| Escala imposible / física rota | Lo imposible tratado como normal | [veo], solo como acento |

## Movimientos de cámara

| Movimiento | Duración | Cómo |
|---|---|---|
| Snap zoom (de abierto a cerrado sin easing) | 0,3 s | [edit] `zoom: [[t,1],[t+0.3,1.6]]` |
| Punch-in lento | 2–4 s | [edit] `zoom` 1 → 1,12 |
| Whip pan con motion blur | 0,5 s | [edit] `xfade` `hblur`/`slideleft` entre tomas + whoosh; [veo] dentro de una toma |
| Paneo o reencuadre | 1–3 s | [edit] keyframes `x`/`y` |
| Dutch snap (giro de 30°) | 0,3 s | [nuevo] (falta rotación en `compose.py`); en capa HTML sí se puede rotar el texto |
| Pull-back reveal | 2 s | [edit] `zoom` 1,5 → 1 si el material tiene resolución; [veo] |
| Órbita / subida (rise) | 2–3 s | [grabar] o [veo] |
| Parallax de foto | 2–4 s | [edit] `depth.py` + capa WebGL |
| Rampa de velocidad (rápido → lento en el momento clave) | — | [edit] partir el clip y poner `speed` distinto; mejor con 60 fps |

## Luz (para pedir tomas o prompts de Veo)

- **Contraluz dorado / silueta:** el sol detrás del sujeto, borde de luz, cara en sombra. Genera curiosidad.
- **Hora dorada lateral:** luz cálida rasante, sombras largas. La mejor para piel y textura (el amanecer del entrenamiento).
- **Neón de dos colores:** lima y coral (los de la marca) desde lados opuestos; para planos de producto de noche.
- **Estrobo:** congela el movimiento a golpes; solo con [veo] o grabado así.

## Capas de sonido (siempre en este orden)

1. **Ambiente:** el sonido real de la toma (pasos, respiración, ciudad) bajo, o silencio a propósito.
2. **Impactos:** whoosh en las transiciones, golpe de bajo en los datos y en los cortes clave, clic en la entrada de texto.
3. **Música:** entra al beat 1–2 s después del hook; ducking bajo la voz.
4. **Voz:** la real del material primero; la voz en off con Chatterbox, solo si suma.

## Prompt de Veo (estructura)

```
[Formato] Vertical 9:16, 8 s, fotorrealista.
[Sujeto y acción] …
[0–2 s] encuadre + movimiento de cámara + qué pasa
[2–5 s] …
[5–8 s] …
[Cámara] lente (24/35/85 mm), altura, movimiento (dolly, órbita, handheld), velocidad
[Luz] hora, dirección, color (paleta de brand.md)
[Sonido] ambiente + impactos (o "sin audio" si lo pone la mezcla)
[Evitar] texto, logos y marcas en la imagen; caras de personas reales; manos deformes
```
