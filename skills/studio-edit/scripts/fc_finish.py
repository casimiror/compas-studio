"""Lleva el montaje a FilmCraft para retoques finales: importa el .otio de `compose.py --stage final --otio`,
pone la secuencia al tamaño y fps del edit.json, aplica el volumen de cada audio (OTIO no lo lleva) y guarda un .fcproj.

Uso: python3 -I fc_finish.py edit.json timeline.otio salida.fcproj
Luego: filmcraft-open salida.fcproj   (abre la app con el canal de control; el MCP `filmcraft` la maneja)
"""
import json
import subprocess
import sys
from pathlib import Path

CLI = str(Path.home() / ".local/bin/filmcraft-cli")


def cli(*args, project=None, save=False):
    cmd = [CLI, "--compact"]
    if project:
        cmd += ["--project", str(project)]
    if save:
        cmd += ["--save"]
    r = subprocess.run(cmd + list(args), capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"filmcraft-cli {' '.join(args)}: {r.stderr.strip() or r.stdout.strip()}")
    lines = [json.loads(l) for l in r.stdout.splitlines() if l.strip().startswith(("{", "["))]
    return lines[0] if len(lines) == 1 else lines


spec_path, otio_path, out = (Path(p).resolve() for p in sys.argv[1:4])
spec = json.loads(spec_path.read_text())
W, H = spec["size"]
fps = spec.get("fps", 30)
out.parent.mkdir(parents=True, exist_ok=True)

res = cli("--save-as", str(out), "import", str(otio_path))
doc = res["documents"][0]
if doc["offlineMedia"]:
    print("ojo, media sin enlazar:", doc["offlineMedia"])

steps = [{"id": "sequence.settings", "params": {"width": W, "height": H, "fps": fps}}]
seq = cli("inspect", "sequence", project=out)
gains = {}  # (nombre, frame de inicio) -> dB
for A in spec.get("audio", []):
    gains[(Path(A["src"]).stem, round(A.get("start", 0) * fps))] = A.get("gain", 0)
for tr in seq["audio"]:
    for it in tr["items"]:
        f = it["startFrame"]  # OTIO redondea al frame: se acepta ±1
        db = (spec.get("base_gain", 0) if tr["name"] == "base"
              else next((gains[k] for k in [(it["name"], f), (it["name"], f + 1), (it["name"], f - 1)] if k in gains), None))
        if db:
            steps.append({"id": "clip.audioGain", "params": {"clips": [it["clip"]], "mode": "set", "db": db}})

# Los clips llegan con la posición de la secuencia por defecto (1920x1080): se recentran al nuevo tamaño.
vids = [it["clip"] for tr in seq["video"] for it in tr["items"]]
steps.append({"id": "clip.fitToFrame", "params": {"clips": vids}})

script = out.with_suffix(".setup.jsonl")
script.write_text("".join(json.dumps(s) + "\n" for s in steps))
cli("run", str(script), project=out, save=True)
seq = cli("inspect", "sequence", project=out)
print(f"listo: {out}  ({W}x{H} @ {fps}, {len(seq['video'])} pistas de video, {len(seq['audio'])} de audio, "
      f"{len(steps) - 1} volúmenes aplicados)")
