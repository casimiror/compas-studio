---
name: studio-concept
description: >
  Propone cómo debe ser un video antes de producirlo: lee el material (hojas de contacto, transcript, fotos, datos),
  el propósito y la marca, y entrega 2 o 3 conceptos distintos, cada uno con hook del frame 0, estructura por tiempos con
  las tomas exactas, el efecto firma, sonido, textos y lo que habría que generar con Gemini; recomienda uno. Úsala cuando
  el usuario pase material y pregunte "qué hacemos con esto", "propón el video", o como paso de concepto del agente compas-studio.
---

# studio-concept

El concepto se decide **antes** del storyboard. Un buen concepto sale del material, no de una plantilla:
qué tiene de especial lo que se grabó (la luz, la historia, un dato, una persona) y cómo el video lo hace evidente en 1 s.

## Entradas (todas antes de proponer)

1. **Propósito y destino**: para quién es, dónde se publica, qué tiene que hacer quien lo ve. Si falta, propón igual y pregúntalo
   junto con los conceptos (no bloquees).
2. **Material**: `analyze.py` a cada video y mira cada `contact.jpg`; lee el transcript (ojo: whisper inventa frases en tomas sin voz,
   como "Gracias por ver el video"). Fotos e imágenes con Read; un PNG con alfa se mira sobre fondo oscuro.
   Por toma anota: resolución real (lo que esté por debajo de 1080 de ancho en vertical solo sirve corto, chico o tratado),
   estabilidad, luz, si hay sujeto claro para `mask.py`, si hay voz útil, y quién sale (terceros = permiso para publicar).
3. **Marca**: `brand.md` del proyecto. Para Compas, además `strategy.md` y `compas-reels`.
4. **Referencias (opcional, cuesta créditos de vidIQ)**: 1–3 outliers del tema con `vidiq_instagram_tiktok_outlier_search`
   para robar estructura, nunca contenido.

## Cada concepto lleva

```
NOMBRE — la idea en una línea
PARA QUÉ SIRVE: qué siente o hace quien lo ve (mandarlo, guardarlo, comentar)
HOOK (frame 0): imagen + texto exactos
ESTRUCTURA: 0–2 s / 2–6 s / …  con archivo e in–out de cada toma
EFECTO FIRMA: lo que lo hace memorable y que studio-edit ya sabe hacer (ver abajo)
SONIDO: voz (quién, Chatterbox o la del material), música (ritmo), sfx
TEXTO EN PANTALLA: frases exactas; datos solo de fuentes (Strava, la tienda, stores.json)
GENERAR: imágenes o b-roll con Gemini, con el prompt; o "nada"
RIESGOS: material flojo, permisos, datos por confirmar
DURACIÓN
```

Los conceptos tienen que ser **distintos de verdad** (uno de datos, uno de historia o personas, uno de ritmo o POV, por ejemplo), no
tres variaciones del mismo. Termina con **una recomendación y por qué**, y pregunta solo lo que cambia la decisión.

## Vocabulario

`references/vocabulario.md`: patrones de hook, movimientos de cámara, luz, capas de sonido y la estructura del
prompt de Veo, cada uno marcado como [edit], [veo], [grabar] o [nuevo]. Úsalo para que los conceptos no repitan siempre
el mismo recurso y para escribir los prompts de Gemini.

## Efectos que studio-edit ya hace (úsalos como vocabulario)

- Texto gigante **detrás** del sujeto (máscara SAM/YOLO) — el sujeto queda delante del dato.
- Etiquetas, flechas o números que **siguen** a una persona u objeto (`track.json`).
- Subtítulos palabra a palabra con la palabra activa resaltada.
- Contadores y datos animados (count-up, barras, anillos) en HTML/GSAP, con los números de la fuente.
- Punch-in y paneo lentos, reencuadre de horizontal a vertical, fondo desenfocado para material de otro formato.
- Cortes al beat de la música (`analyze.py --beats`), cámara lenta (`speed` < 1, mejor con material de 60 fps), transiciones xfade.
- Parallax 2.5D sobre una foto (`depth.py`).
- Recorte del sujeto sobre un fondo nuevo (color de marca o imagen generada).

Si un concepto necesita algo que no está en la lista (mapa de ruta animado, seguimiento de cámara 3D, cambio de cielo), dilo como
"nuevo, hay que construirlo" y estima el esfuerzo; no lo prometas como hecho.
