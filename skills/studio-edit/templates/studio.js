// Ayudas compartidas de las capas de motion de compas-studio.
// La página carga antes data.js (window.STUDIO = {words, track}), hecho con scripts/pack.py.
(function () {
  const S = window.STUDIO || { words: [], track: null };

  // Posición del sujeto en el segundo t (interpola entre frames del track.json). null si no está.
  S.trackAt = function (t) {
    const tr = S.track;
    if (!tr || !tr.frames.length) return null;
    const i = Math.min(tr.frames.length - 1, Math.max(0, Math.floor(t * tr.fps)));
    const a = tr.frames[i], b = tr.frames[Math.min(i + 1, tr.frames.length - 1)];
    if (!a.box) return null;
    if (!b.box) return a;
    const k = t * tr.fps - i, l = (x, y) => x + (y - x) * k;
    return { cx: l(a.cx, b.cx), cy: l(a.cy, b.cy), top: l(a.top, b.top),
             box: a.box.map((v, j) => l(v, b.box[j])) };
  };

  // Suaviza el track (media móvil) para que lo que sigue al sujeto no tiemble.
  S.smoothTrack = function (win = 5) {
    const f = S.track && S.track.frames;
    if (!f) return;
    const keys = ['cx', 'cy', 'top'];
    const out = f.map((fr, i) => {
      if (!fr.box) return fr;
      const n = f.slice(Math.max(0, i - win), i + win + 1).filter(x => x.box);
      const avg = {};
      keys.forEach(k => { avg[k] = n.reduce((s, x) => s + x[k], 0) / n.length; });
      return { ...fr, ...avg };
    });
    S.track.frames = out;
  };

  // Agrupa las palabras en frases cortas para subtítulos (máximo `max` palabras, corta en pausas y puntuación).
  S.chunks = function (max = 3, gap = 0.35) {
    const out = [];
    let cur = [];
    (S.words || []).forEach((w, i, all) => {
      cur.push(w);
      const next = all[i + 1];
      const pause = next && next.s - w.e > gap;
      if (cur.length >= max || pause || /[.,!?¿¡;:]$/.test(w.w) || !next) {
        out.push({ s: cur[0].s, e: cur[cur.length - 1].e, words: cur });
        cur = [];
      }
    });
    return out;
  };

  // window.__clip con el contrato de webclip: el timeline de GSAP más una función que corre en cada seek
  // (para lo que depende del track, que no es un tween).
  S.exportClip = function (tl, onSeek) {
    window.__clip = {
      duration: () => tl.duration(),
      seek: (t) => { tl.seek(t, false); if (onSeek) onSeek(t); },
    };
    const t0 = performance.now();
    (function loop() {
      if (window.__renderMode) return;
      window.__clip.seek(((performance.now() - t0) / 1000) % tl.duration());
      requestAnimationFrame(loop);
    })();
  };

  window.STUDIO = S;
})();
