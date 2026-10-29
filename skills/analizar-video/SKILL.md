---
name: analizar-video
description: Analiza un video corto (reel, TikTok, Short) que funcionó o que se quiere copiar, propio o ajeno, y saca la fórmula para repetirlo. Desarma el video segundo a segundo (gancho del frame 0, cortes, texto en pantalla, audio, loop), lee las métricas (vistas, likes, comentarios, reposts, envíos y sus proporciones), explica por qué funcionó y busca con vidIQ reels virales del mismo formato para sacar ganchos probados. Entrega el análisis, la fórmula y de 5 a 10 ganchos nuevos listos para grabar. Úsala cuando el usuario pase un video o una grabación de pantalla y pida "analiza este video", "por qué le fue bien", "qué tiene este reel", "quiero otro como este" o ganchos virales.
---

# Analizar un video corto

El objetivo no es describir el video: es **sacar la fórmula que se puede repetir** y convertirla en ganchos y guiones nuevos.
Para escribir y producir el siguiente reel, la skill `reel-craft` (oficio) y, en Compas, `compas-reels` (nicho y estrategia).

## 1. Desarmar el video (gratis, local)

Trabaja en el scratchpad o en la carpeta de análisis, nunca dentro del archivo original.

```bash
F="ruta/al/video.mp4"
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of compact "$F"
# hoja de contacto: 1 cuadro por segundo, 6 columnas (24 cuadros por hoja)
ffmpeg -v error -i "$F" -vf "fps=1,scale=270:-1,tile=6x4" hoja-%02d.jpg
# cortes de escena (tiempos donde cambia el plano)
ffmpeg -i "$F" -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep -o 'pts_time:[0-9.]*'
# primer cuadro (el gancho) en grande
ffmpeg -v error -ss 0 -i "$F" -frames:v 1 frame0.jpg
```

- Mira las hojas con Read. Para el texto que dice el video: el texto en pantalla se lee en los cuadros, y si hay voz,
  transcribe con mlx-whisper (como en `studio-edit`).
- **Si es una grabación de pantalla del propio reel** (iPhone): recorta lo que no es del reel (navegación, Centro de control,
  pantalla de inicio) y lee las métricas de la interfaz: vistas, likes, comentarios, reposts y envíos.
  En Instagram, los íconos de la derecha van de arriba abajo: likes, comentarios, reposts, envíos.
- **Si es un link**: con el link se puede usar `vidiq_watch_shortform_content` (10 créditos), pero solo si no se puede
  conseguir el archivo o una grabación de pantalla.

## 2. Ficha del video

Guarda el análisis como `analisis-videos/AAAA-MM-DD-<slug>.md` en la carpeta de marketing del proyecto
(`<marketing>/reels/analisis-videos/`). Secciones:

1. **Datos:** cuenta, fecha, duración, formato (vertical, pantalla dividida…), audio (canción en tendencia, voz, original), caption y hashtags.
2. **Métricas y proporciones:**
   - envíos / vistas y reposts / vistas: son las señales que más empujan el alcance a no seguidores. Más de 0,5 % es muy bueno.
   - likes / vistas (3–5 % es normal) y comentarios / vistas.
   - Comparar con la mediana de la cuenta: un reel que hace 10x la mediana es un outlier y su formato vale oro.
3. **Mapa segundo a segundo:** tabla `segundo | qué se ve | texto en pantalla | audio | por qué retiene`.
4. **Gancho:** qué hay en el frame 0 y en los primeros 3 s (imagen, texto, sonido). ¿Se entiende sin sonido?
5. **Estructura y ritmo:** cada cuánto hay cortes o cambios de patrón, arco emocional (problema → tensión → resolución).
6. **Loop:** ¿el final empalma con el principio? Un loop limpio suma reproducciones repetidas.
7. **Por qué funcionó:** de 3 a 5 razones concretas, cada una amarrada a algo que se ve en el video o en las métricas.
8. **Fórmula repetible:** la plantilla sin el tema, en una línea (ej. "pantalla dividida: escena de anime emotiva con subtítulos
   arriba + yo entrenando abajo + canción en tendencia + loop").
9. **Riesgos:** derechos de autor (clips de anime, películas, música), cosas que solo funcionan en una cuenta personal y no en una marca.

## 3. Buscar el patrón afuera con vidIQ (cuesta créditos)

Los créditos son pocos (150 al mes). **Primero `vidiq_balance` (gratis).** Presupuesto por análisis: de 5 a 15 créditos.

1. `vidiq_instagram_tiktok_outlier_search` (5 créditos), con `embeddingType: "format"` y la fórmula del paso 2.8 como `query`.
   `audienceQuery` con la región y el público real (ej. `Culture/Region: Latin America/Colombia; Global: true; Demographics: ...;`),
   `descriptionLanguage: ["es","en"]` y `datePostedAfter` de los últimos 3 meses. Devuelve reels que hicieron 10x o más su mediana,
   con el gancho de 0 a 3 s de cada uno.
2. Solo si hace falta ver el detalle de uno: `vidiq_watch_shortform_content` (10 créditos) sobre el mejor outlier.
3. Con `embeddingType: "hook"` se buscan ganchos en vez de formatos, para cuando el formato ya está claro.
4. `vidiq_generate_titles` es para títulos de YouTube: no sirve para ganchos de reels.

Anota en la ficha una tabla de los outliers: `cuenta | vistas | x mediana | gancho (texto 0-3 s) | qué copia de la fórmula`.
Se necesitan al menos 2 outliers del mismo formato para llamarlo patrón.

## 4. Ganchos y siguiente video

Con la fórmula y los outliers, escribe **de 5 a 10 ganchos nuevos** (los redacta Claude: vidIQ no genera ganchos de reels):
- Menos de 10 palabras, legibles en el frame 0, en el tono de la cuenta.
- Cada gancho con: tipo (curiosidad, contraste, identificación, shock), la escena o clip que lo acompaña, y qué se graba.
- Marca cuál vale para la cuenta personal y cuál para la marca, y adapta los riesgos (en una marca, nada de clips con derechos
  de autor: se reemplazan por material propio o por animación).

Cierra con **el siguiente video recomendado** en el formato de guion de `reel-craft`, y agrégalo como propuesto
al calendario de la empresa (sección "Plan de la semana" de su skill de contenido, si tiene).
