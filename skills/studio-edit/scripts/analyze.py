"""Analiza un video: metadatos, cortes de escena, transcript palabra a palabra, beats y hoja de contactos.

Uso: ~/.venvs/studio/bin/python -I analyze.py <video> <carpeta_salida> [--no-words] [--beats] [--lang es]

Escribe en la carpeta: analysis.json, words.json (si hay voz), contact.jpg.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    d = json.loads(out)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    info = {"duration": float(d["format"]["duration"]), "has_audio": a is not None}
    if v:
        num, den = v["r_frame_rate"].split("/")
        rot = 0
        for sd in v.get("side_data_list", []):
            rot = int(sd.get("rotation", rot))
        w, h = v["width"], v["height"]
        if abs(rot) in (90, 270):
            w, h = h, w
        info.update(width=w, height=h, fps=round(int(num) / int(den), 3), codec=v["codec_name"])
    return info


def scenes(path):
    from scenedetect import ContentDetector, detect

    return [[round(s.get_seconds(), 3), round(e.get_seconds(), 3)] for s, e in detect(str(path), ContentDetector())]


def extract_wav(path, wav):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)


def words(wav, lang):
    """Transcript palabra a palabra con el motor que este equipo puede correr (ver equipo.py)."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from equipo import perfil

    p = perfil()
    ws = []
    if p["whisper"] == "mlx":
        import mlx_whisper

        r = mlx_whisper.transcribe(
            str(wav), path_or_hf_repo=f"mlx-community/whisper-{p['whisper_modelo']}", language=lang, word_timestamps=True
        )
        for seg in r["segments"]:
            for w in seg.get("words", []):
                ws.append({"w": w["word"].strip(), "s": round(w["start"], 3), "e": round(w["end"], 3)})
        return r["text"].strip(), ws
    if p["whisper"] == "faster-whisper":
        from faster_whisper import WhisperModel

        dev = "cuda" if p["acelerador"] == "cuda" else "cpu"
        model = WhisperModel(p["whisper_modelo"], device=dev, compute_type="float16" if dev == "cuda" else "int8")
        segs, _ = model.transcribe(str(wav), language=lang, word_timestamps=True)
        text = []
        for seg in segs:
            text.append(seg.text)
            for w in seg.words or []:
                ws.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})
        return "".join(text).strip(), ws
    raise SystemExit("analyze: no hay motor de transcripción; instala mlx-whisper (Mac Apple Silicon) o faster-whisper (los demás)")


def beats(wav):
    import librosa

    y, sr = librosa.load(str(wav), sr=22050)
    tempo, frames = librosa.beat.beat_track(y=y, sr=sr)
    onset = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    return {"tempo": float(tempo), "beats": [round(float(t), 3) for t in librosa.frames_to_time(frames, sr=sr)],
            "onsets": [round(float(t), 3) for t in onset]}


def contact_sheet(path, dur, out, n=24, cols=6):
    from PIL import Image, ImageDraw

    with tempfile.TemporaryDirectory() as tmp:
        tiles = []
        for i in range(n):
            t = dur * (i + 0.5) / n
            f = Path(tmp) / f"{i}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
                            "-vf", "scale=240:-2", str(f)], check=True)
            if f.exists():
                im = Image.open(f).convert("RGB")
                ImageDraw.Draw(im).rectangle([0, 0, 64, 18], fill="black")
                ImageDraw.Draw(im).text((4, 3), f"{t:5.2f}s", fill="white")
                tiles.append(im)
        if not tiles:
            return
        tw, th = tiles[0].size
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th), "black")
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
        sheet.save(out, quality=85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--no-words", action="store_true")
    ap.add_argument("--beats", action="store_true")
    ap.add_argument("--lang", default="es")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    info = probe(a.video)
    is_video = "width" in info
    if is_video:
        info["scenes"] = scenes(a.video)
    if info["has_audio"]:
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "a.wav"
            extract_wav(a.video, wav)
            if not a.no_words:
                info["text"], ws = words(wav, a.lang)
                (out / "words.json").write_text(json.dumps(ws, ensure_ascii=False, indent=0))
                info["words"] = len(ws)
            if a.beats:
                info["music"] = beats(wav)
    if is_video:
        contact_sheet(a.video, info["duration"], out / "contact.jpg")
    (out / "analysis.json").write_text(json.dumps(info, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in info.items() if k != "music"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
