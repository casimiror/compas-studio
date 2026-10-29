"""Empaqueta words.json y track.json en data.js para las plantillas de motion (window.STUDIO).

Uso: python3 pack.py <salida/data.js> [--words words.json] [--track track.json] [--offset 0] [--extra extra.json]
--offset resta segundos a todo (si la capa empieza más tarde que el video base).
"""
import argparse
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--words")
ap.add_argument("--track")
ap.add_argument("--offset", type=float, default=0)
ap.add_argument("--extra", help="JSON con datos propios del video (textos, tiendas…), queda en STUDIO.extra")
a = ap.parse_args()

data = {"words": [], "track": None}
if a.words:
    data["words"] = [{**w, "s": round(w["s"] - a.offset, 3), "e": round(w["e"] - a.offset, 3)}
                     for w in json.loads(Path(a.words).read_text()) if w["e"] > a.offset]
if a.track:
    tr = json.loads(Path(a.track).read_text())
    skip = int(a.offset * tr["fps"])
    tr["frames"] = [{**f, "t": round(f["t"] - a.offset, 3)} for f in tr["frames"][skip:]]
    data["track"] = tr
if a.extra:
    data["extra"] = json.loads(Path(a.extra).read_text())
Path(a.out).write_text("window.STUDIO = " + json.dumps(data, ensure_ascii=False) + ";\n")
print(f"listo: {a.out} ({len(data['words'])} palabras, track {'sí' if data['track'] else 'no'})")
