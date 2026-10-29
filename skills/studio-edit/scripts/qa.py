"""Revisión antes de entregar: medidas, volumen, frames negros o congelados, y hojas para mirar.

Uso: ~/.venvs/studio/bin/python -I qa.py <video> <carpeta_salida> [--n 18] [--ig]

Escribe: qa.json, sheet.jpg (hoja de contactos con zonas seguras de Instagram si --ig),
frame0.png, mid.png, last.png. Mira las imágenes con Read antes de dar el video por terminado.
"""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

# Zonas que tapa la interfaz de Reels en 1080x1920 (aprox.): arriba, abajo y la columna de botones a la derecha.
IG_TOP, IG_BOTTOM, IG_RIGHT = 220, 420, 140


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    d = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path]).stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    num, den = v["r_frame_rate"].split("/")
    return {"duration": round(float(d["format"]["duration"]), 3), "width": v["width"], "height": v["height"],
            "fps": round(int(num) / int(den), 3), "vcodec": v["codec_name"], "pix_fmt": v.get("pix_fmt"),
            "audio": a["codec_name"] if a else None, "size_mb": round(int(d["format"]["size"]) / 1e6, 2)}


def loudness(path):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = err[err.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    p = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    return {"lufs": float(i.group(1)) if i else None, "true_peak": float(p.group(1)) if p else None}


def detect(path):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vf",
               "blackdetect=d=0.15:pix_th=0.06,freezedetect=n=0.002:d=0.8", "-an", "-f", "null", "-"]).stderr
    black = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)
    freeze = re.findall(r"freeze_start: ([\d.]+)", err)
    sil = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "silencedetect=n=-45dB:d=0.6", "-vn", "-f",
               "null", "-"]).stderr
    silences = re.findall(r"silence_start: (-?[\d.]+)", sil)
    return {"black": [[float(a), float(b)] for a, b in black], "freeze_starts": [float(f) for f in freeze],
            "silence_starts": [float(s) for s in silences]}


def grab(path, t, out, scale=None):
    vf = ["-vf", f"scale={scale}:-2"] if scale else []
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(t, 0):.3f}", "-i", path, "-frames:v", "1", *vf, str(out)])
    return out.exists()


def guides(im, W, H):
    d = ImageDraw.Draw(im, "RGBA")
    sx, sy = im.width / W, im.height / H
    d.rectangle([0, 0, im.width, IG_TOP * sy], fill=(255, 0, 0, 60))
    d.rectangle([0, im.height - IG_BOTTOM * sy, im.width, im.height], fill=(255, 0, 0, 60))
    d.rectangle([im.width - IG_RIGHT * sx, IG_TOP * sy, im.width, im.height - IG_BOTTOM * sy], fill=(255, 0, 0, 40))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=18)
    ap.add_argument("--ig", action="store_true", help="dibuja las zonas que tapa la interfaz de Reels")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    info = probe(a.video)
    info.update(loudness(a.video))
    info.update(detect(a.video))
    D, W, H = info["duration"], info["width"], info["height"]

    grab(a.video, 0, out / "frame0.png")
    grab(a.video, D / 2, out / "mid.png")
    grab(a.video, D - 0.1, out / "last.png")

    with tempfile.TemporaryDirectory() as tmp:
        tiles = []
        for i in range(a.n):
            t = D * i / a.n
            f = Path(tmp) / f"{i}.jpg"
            if grab(a.video, t, f, scale=270):
                im = Image.open(f).convert("RGB")
                if a.ig:
                    guides(im, W, H)
                dr = ImageDraw.Draw(im)
                dr.rectangle([0, 0, 70, 18], fill="black")
                dr.text((4, 3), f"{t:5.2f}s", fill="white")
                tiles.append(im)
        cols = 6
        tw, th = tiles[0].size
        sheet = Image.new("RGB", (cols * tw, ((len(tiles) + cols - 1) // cols) * th), "black")
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
        sheet.save(out / "sheet.jpg", quality=85)

    warn = []
    if info["lufs"] is not None and abs(info["lufs"] - (-14)) > 1.5:
        warn.append(f"volumen {info['lufs']} LUFS (objetivo -14)")
    if info["true_peak"] is not None and info["true_peak"] > -0.5:
        warn.append(f"pico {info['true_peak']} dBFS: puede saturar")
    if info["black"]:
        warn.append(f"frames negros: {info['black']}")
    if info["freeze_starts"]:
        warn.append(f"imagen congelada desde: {info['freeze_starts']} (¿intencional?)")
    if info["silence_starts"] and info["silence_starts"][0] < 0.3:
        warn.append("arranca en silencio: el hook necesita sonido desde el frame 0")
    if a.ig and (W, H) != (1080, 1920):
        warn.append(f"medidas {W}x{H}: un reel va en 1080x1920")
    if info["audio"] is None:
        warn.append("sin audio")
    info["warnings"] = warn
    (out / "qa.json").write_text(json.dumps(info, indent=2, ensure_ascii=False))
    print(json.dumps(info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
