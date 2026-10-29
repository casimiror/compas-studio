---
name: reel-craft
description: >
  Oficio de reels y videos cortos verticales (Instagram, TikTok, Shorts) para cualquier marca: qué mide el algoritmo,
  hooks del frame 0, mapa de retención por segundo, cambios de patrón, subtítulos, loop, CTA, investigación con vidIQ
  sin gastar créditos de más, y la lista de chequeo antes de publicar. Úsala al planear, escribir o revisar un reel,
  o cuando el agente compas-studio arme un guion. Para Compas, compas-reels tiene el nicho, la estrategia y los formatos, y manda.
---

# reel-craft

## Qué mide Instagram (lo confirmado)

Mosseri (enero de 2025) nombró las tres señales que más pesan: **tiempo de visualización, likes por alcance y envíos por alcance**.
Los likes pesan más con quienes ya te siguen; **los envíos (mandarlo por DM) pesan más con quienes no te siguen**, que es donde se crece.
En diciembre de 2025 dijo que en 2026 Instagram favorece lo **humano y crudo** sobre lo generado con IA, y lo original sobre los reposts.

Consecuencias para el diseño:
- Cada reel se escribe para que alguien se lo **mande a una persona concreta** ("etiqueta al que siempre se le acaba").
- La base es **material real** (personas, tiendas, producto en mano). Motion, IA y efectos son el acento, no el video entero.
- Nada de marcas de agua de otras apps; nada reciclado de TikTok tal cual.

Lo que repiten los blogs (sin fuente oficial, úsalo como hipótesis y mídelo): ~60 % de retención a los 3 s, métrica de
"skip rate" en los primeros 3 s, 15–30 s para cuentas nuevas.

## Mapa de retención (por defecto 7–15 s; hasta 30 s si hay historia)

| Tiempo | Qué pasa | Regla |
|---|---|---|
| Frame 0 | Hook visual + texto | Ya se ve algo en movimiento y el texto se lee en el frame 0. Nada de logo, intro ni negro. Sonido desde 0 |
| 0–2 s | Promesa | Una tensión concreta: número, ciudad, marca, situación reconocible. ≤ 8 palabras en pantalla |
| Cada 2–3 s | Cambio de patrón | Corte, punch-in, cambio de ángulo, texto nuevo, efecto de sonido. Nunca más de 3 s iguales |
| Medio | Pago | El valor real. Una idea por escena |
| Últimos 1–2 s | CTA + loop | Una sola acción (comentar, guardar, mandar). El último frame empalma con el primero para que se repita |

## Texto y sonido

- Subtítulos siempre (mucha gente ve sin sonido), 2–3 palabras a la vez, la palabra que suena resaltada, dentro de la zona segura
  (1080×1920: nada importante en los 220 px de arriba, los 420 de abajo ni los 140 de la derecha).
- Voz: frases de menos de 12 palabras, ritmo rápido sin atropellar. Música bajo la voz (ducking), voz clara a -14 LUFS en total.
- Efectos de sonido en los cortes y en las entradas de texto: es la mitad del "se siente profesional".
- Audio en tendencia: no se puede poner por código. Si conviene, se deja anotado para que el usuario lo agregue al publicar en la app.

## Hooks que funcionan (tipos)

Curiosidad ("Esto no lo venden en Medellín"), contrarian ("Deja de comprar creatina en el D1"), shock con dato verificado,
POV ("POV: le preguntas el precio a la tienda y…"), lista ("3 tiendas de Quilla que…"), antes/después.
Prohibido el clickbait que el video no cumple: hunde la retención y la confianza.

## Investigación con vidIQ (cuesta créditos: 150 al mes)

- Revisa `vidiq_balance` antes. Agrupa la investigación en una sesión semanal.
- `vidiq_instagram_tiktok_outlier_search` con el tema: reels que superan mucho el promedio de su cuenta = formato probado.
  Copia la **estructura** (hook, ritmo, formato), nunca el contenido.
- `vidiq_watch_shortform_content` sobre 1–3 outliers para sacar el mapa de retención real (qué pasa en cada segundo).
- `vidiq_instagram_owner_insights` si la cuenta está conectada: guardados, envíos y retención de los propios reels.
- Voz, b-roll y música de vidIQ: no. Voz con Chatterbox local; b-roll grabado o generado.

## Chequeo antes de publicar

- [ ] El frame 0 se entiende sin sonido y sin contexto.
- [ ] Hay un cambio visual o sonoro cada ≤ 3 s (mira la hoja de contactos de `qa.py`).
- [ ] Subtítulos sincronizados, sin texto cortado, fuera de las zonas de la interfaz.
- [ ] -14 LUFS ±1.5, pico < -1 dBFS, sin silencio inicial.
- [ ] Un solo CTA. El final empalma con el inicio.
- [ ] Todo dato en pantalla tiene fuente; nada inventado (tiendas, precios, testimonios).
- [ ] Portada (frame o imagen) legible en la grilla 3:4 del perfil.
- [ ] Caption: hook en la primera línea, pregunta para comentar, 3–5 hashtags específicos.

## Medir

A las 24 h y a los 7 días: retención media y a los 3 s, envíos por alcance, guardados, likes por alcance, visitas al perfil.
Anota qué hook y qué formato tuvo cada reel para saber qué repetir.
