"""Recorte de precisión de una persona en video con MatAnyone 2 (alfa suave: pelo, dedos, bordes en movimiento).
Úsalo solo cuando el borde de YOLO no alcance (planos cerrados, cambio de fondo completo); YOLO sigue siendo el motor principal.

Uso: ~/.venvs/studio/bin/python -I matting.py <video> <carpeta_salida> [--mask m.png] [--max-size 1080]
- Sin --mask, YOLO-seg crea la máscara del primer frame (la persona más grande). Si la persona sostiene un objeto
  (mancuerna, producto) MatAnyone lo deja fuera: pasa una --mask que lo incluya (mask.py --engine sam2 sobre el frame 0).
Salida: alpha.mp4 (alfa en gris), subject.mov (ProRes 4444 con alfa), mask0.png
Tiempo: ~1,4 s por frame a 1080x1920 en M1 Pro (3 s de video ≈ 2 min 20 s). --max-size 720 lo acelera.
"""
import argparse, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("out")
ap.add_argument("--mask"); ap.add_argument("--max-size", type=int, default=-1)
a = ap.parse_args()
out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
SRC = Path.home() / ".venvs/matanyone2-src"; PY = Path.home() / ".venvs/matanyone/bin/python"
tmp = Path(tempfile.mkdtemp(prefix="matting-", dir=out))
frames = tmp / "frames"; frames.mkdir()
# MatAnyone 2 lee carpetas de frames (el torchvision actual ya no trae read_video)
a.video = str(Path(a.video).resolve())
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.video, str(frames / "%05d.png")], check=True)
mask0 = out / "mask0.png"
if a.mask:
    shutil.copy(Path(a.mask).resolve(), mask0)
else:
    import cv2, numpy as np
    from ultralytics import YOLO
    m = YOLO(str(Path.home() / ".cache/studio-models/yolo11m-seg.pt"))
    f0 = cv2.imread(str(frames / "00001.png"))
    r = m(f0, classes=[0], retina_masks=True, verbose=False)[0]
    if r.masks is None:
        sys.exit("YOLO no encontró persona en el frame 0: pasa --mask")
    ms = r.masks.data.cpu().numpy(); k = int(np.argmax(ms.reshape(len(ms), -1).sum(1)))
    cv2.imwrite(str(mask0), cv2.resize((ms[k] > 0.5).astype(np.uint8) * 255, (f0.shape[1], f0.shape[0])))
cmd = [str(PY), "-I", "inference_matanyone2.py", "-i", str(frames), "-m", str(mask0), "-o", str(tmp / "res")]
if a.max_size > 0:
    cmd += ["--max_size", str(a.max_size)]
subprocess.run(cmd, cwd=SRC, check=True)
pha = next((tmp / "res").glob("*_pha.mp4"))
fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                      "-of", "csv=p=0", a.video], capture_output=True, text=True).stdout.split()[0].strip(",")
w, h = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                       "-of", "csv=p=0", a.video], capture_output=True, text=True).stdout.split()[0].split(",")[:2]
# la salida viene con ancho redondeado a múltiplo de 16: se reescala al tamaño del video
subprocess.run(["ffmpeg", "-y", "-v", "error", "-r", fps, "-i", str(pha), "-vf", f"scale={w}:{h},format=gray",
                "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(out / "alpha.mp4")], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-i", str(out / "alpha.mp4"), "-filter_complex",
                "[1:v]format=gray[a];[0:v][a]alphamerge", "-an", "-c:v", "prores_ks", "-profile:v", "4444",
                "-pix_fmt", "yuva444p10le", str(out / "subject.mov")], check=True)
shutil.rmtree(tmp)
print(f"listo: {out}/alpha.mp4, {out}/subject.mov")
