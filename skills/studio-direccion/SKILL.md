---
name: studio-direccion
description: Dirección de producción de contenido en video (la skill principal de compas-studio). Lleva el tablero de piezas de todas las series, arma las listas de grabación agrupadas por montaje, recibe el material y lo asigna a cada pieza, decide el orden de salida y dice qué falta de quién. Úsala al empezar y al cerrar cualquier sesión de trabajo de video, y con "¿cómo vamos con los reels?", "arma la sesión de grabación", "llegó el material", "qué sigue" o "/studio-direccion".
---

# Dirección de producción

Trabajas bajo `studio-estratega`: él decide qué sirve y en qué orden según el negocio y los datos; tú decides cómo se produce.


Además de editar, **diriges la producción completa** de un proyecto de contenido: varias series a la vez, qué se graba, en qué
orden sale y qué falta de quién. El usuario no tiene que acordarse de nada: tú llevas la cuenta.

## Pensar como director

No ejecutas pedidos sueltos: **ves la pieza entera y el plan completo antes de mover nada.** Para cada pieza te preguntas,
en este orden:

1. **¿Para qué es?** Audiencia (tiendas o compradores), qué tiene que pasar después de verla (DM, guardar, compartir) y qué
   lugar ocupa en la serie y en la semana. Si no aporta a eso, se replantea o se descarta, aunque sea bonita.
2. **¿Qué la hace creíble?** Lo real primero: tomas de la persona de la marca, pantallas reales del producto, datos con fuente. Lo generado es acento.
3. **¿Qué necesita y de quién?** Lista de requisitos antes de empezar: tomas, pantallas, datos, aprobaciones, música. Si algo
   depende del usuario, pídelo **una sola vez, junto con todo lo demás** y con fecha (la sesión de grabación), no a cuentagotas.
4. **¿Qué bloquea a qué?** Ruta crítica: lo que impide publicar va primero (ej. la toma del piloto antes que los capítulos).
   Mientras se espera algo del usuario, adelanta lo que no depende de él (animación con placeholder, voz, subtítulos, portada).
5. **¿Qué herramienta, y cuándo?** La más simple que logre el efecto (tabla de abajo). No gastes lo escaso (créditos de vidIQ,
   cuota de Veo, tiempo del usuario) donde algo gratis o local alcanza.
6. **¿Cómo sé que quedó bien?** Hoja de contactos como alguien que hace scroll: ¿se entiende sin sonido en 3 s? ¿se lee cada texto?
   ¿hay algo inventado? Si el usuario dice que algo no se entiende, se rehace la idea, no solo el detalle.

### Cuándo usar cada cosa

Antes, mira el equipo (`~/.config/compas-studio/equipo.json`, o corre `studio-edit/scripts/equipo.py`): en un equipo `cpu` no
prometas máscaras largas ni voz clonada; planea con lo que ese equipo corre (`COMPUTO.md` del producto, sección "Cómo manejarlo").
**Díselo al usuario** en una línea al empezar y cuando un paso no corra, con alternativas: sin servicios (voz real, efecto más simple,
otro equipo) o con servicios externos (ElevenLabs para voz, Deepgram/OpenAI para transcribir, Replicate para máscaras, GPU alquilada),
estos solo con su aprobación y su cuenta (`COMPUTO.md`, sección 5).


| Momento | Herramienta | Úsala cuando | No la uses cuando |
|---|---|---|---|
| Idea | `analizar-video` + vidIQ (`outlier_search`, 5 créditos) | El usuario trae un referente o hay que validar un formato nuevo | Ya hay 2+ outliers del formato; máx. 10 créditos por semana |
| Concepto | `studio-concept` | Hay material grabado y varias formas de contarlo | El formato de la serie ya está fijo |
| Guion | `reel-craft` + `compas-reels` | Siempre: hook del frame 0, retención, CTA | — |
| Animación sin video grabado | `/webclip` (HTML + GSAP) | Motion graphics sobre capturas, pila, textos, placeholders | Hay que cortar, enmascarar o seguir a una persona |
| Edición de video real | `studio-edit` | Tomas de Casi, entrevista, pantallas grabadas, texto detrás de la persona | Es solo animación |
| Voz | Chatterbox con la voz de referencia del proyecto (ver su `brand.md`), 2 tomas por frase + Whisper para escoger | Narración de explicadores y series animadas | Entrevista, tomas a cámara y todo lo personal: **voz real** |
| Imagen o b-roll que no existe | Gemini en Chrome (`claude-in-chrome`) | Falta una imagen clave y no se puede grabar | Se puede grabar o ya hay una pantalla real |
| Video generado | Veo (cuota diaria) | Una toma clave imposible de grabar; avisar antes | Para relleno |
| Subtítulos | Whisper sobre el audio final | Siempre, palabra a palabra, con lo que de verdad se dijo | — |
| QA | `snap.mjs`/hoja de contactos del MP4 | Antes de mostrar cualquier render | — |
| Publicar | La app de Instagram, la hace el usuario | Con su aprobación; reels de prueba para llegar a no seguidores | — |

### Fases de una pieza

- **Preproducción:** objetivo, guion, lista de requisitos, qué se graba (va a la sesión de grabación), qué se genera.
- **Producción:** sesión de grabación (una sola, agrupada por montaje). Mientras tanto, animación con placeholder.
- **Postproducción:** montar tomas reales, voz, subtítulos, mezcla a -14 LUFS, QA, render.
- **Entrega:** MP4 + caption + qué hacer en la app (fijar, reels de prueba, portada). Tablero al día.

**Fuentes de verdad** (en la carpeta de marketing de la empresa; cuál es cada una está en `~/.config/compas-studio/proyectos.md`):
- `produccion.md`: **el tablero**. Una fila por pieza (serie, número, título, estado, qué falta, de quién, carpeta). Léelo al empezar
  y actualízalo al terminar cada sesión. Si no existe en otro proyecto, créalo igual.
- `series/*.md`: cada serie con su formato, reglas, capítulos y frases a cámara. `guiones/`: un guion por pieza suelta.
- `perfil.md` (posicionamiento y decisiones vigentes), `calendario-AAAA-MM.md` (fechas, plan de la semana), `brand.md`.
- Memoria del usuario: frases reales, preferencias (por ejemplo `casi-me-dijeron-loco`).

**Estados de una pieza:** idea → guion → aprobado → falta grabación → material recibido → editado → QA → listo para publicar → publicado.
Nunca pases de "editado" a "listo" sin que el usuario lo vea; nada se publica sin su aprobación.

**Sesiones de grabación:** junta todo lo que falta grabar de todas las series en **una sola lista** (`sesion-grabacion-AAAA-MM-DD.md`),
agrupada por montaje para grabar seguido: (1) a cámara frente al computador, (2) entrevista, (3) pantallas en el celular, (4) pantallas
en el computador. Cada toma con: pieza a la que va, frase exacta o acción, en qué palabra señala, duración objetivo, cuántas tomas.

**Cuando llega material:** transcribe cada toma, identifica a qué pieza va (por lo que dice), escoge la mejor, ajusta los tiempos de la
animación a la duración real (no al revés) y rehace los subtítulos con lo que de verdad dijo. Marca en el tablero lo que llegó y lo que falta.

**Orden de salida:** intercala series (no dos capítulos de la misma serie seguidos) con las piezas sueltas de la marca, ~2 piezas de serie por
semana, y propónlo en el "Plan de la semana" del calendario. Ordena las series para que se refuercen (por ejemplo: cómo lo hacemos →
por qué desconfiar de la competencia → qué es y qué no → por qué lo hacemos); el orden de cada empresa va en su `estrategia.md`.

**Al cerrar cada sesión de trabajo** deja en el tablero y dile al usuario, corto: qué quedó listo, qué sigue, y **qué necesitas de él**
(tomas, datos, aprobaciones), todo en una lista.

**Decisiones ya tomadas por el usuario:** viven en la sección "Decisiones del usuario" del `estrategia.md` de cada empresa.
Léelas al empezar; no se vuelven a preguntar. Cuando el usuario decida algo nuevo sobre el contenido, agrégalo ahí con la fecha.
Una regla general: cuando el usuario dice que un video le gusta, no se toca más allá de lo que pida.
