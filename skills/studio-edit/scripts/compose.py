"""Arma el video desde un edit.json con ffmpeg, en dos etapas.

Uso:
  ~/.venvs/studio/bin/python -I compose.py edit.json --stage base  --out base.mp4   # cortes, reencuadre, color, transiciones
  ~/.venvs/studio/bin/python -I compose.py edit.json --stage final --out final.mp4  # base + capas con alfa + audio mezclado
  ... --otio timeline.otio   # además exporta la línea de tiempo (FilmCraft, Resolve, Kdenlive)
  ... --dry                  # solo imprime el comando de ffmpeg

Las rutas del edit.json son relativas al propio edit.json. El formato está en references/edit-spec.md.
"""
import argparse
import json
import shlex
import subprocess
from pathlib import Path


IMAGES = {".jpg", ".jpeg", ".png", ".webp"}


def has_audio(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return bool(out.strip())


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def esc(s):
    return str(s).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def lerp_expr(keys, default):
    """[[t, v], ...] -> expresión de ffmpeg con interpolación lineal en t."""
    if not keys:
        return str(default)
    keys = sorted(keys)
    if len(keys) == 1:
        return str(keys[0][1])
    expr = str(keys[-1][1])
    for (t0, v0), (t1, v1) in reversed(list(zip(keys, keys[1:]))):
        seg = f"({v0}+({v1}-{v0})*(t-{t0})/({t1}-{t0}))"
        expr = f"if(lt(t\\,{t1})\\,{seg}\\,{expr})"
    return f"if(lt(t\\,{keys[0][0]})\\,{keys[0][1]}\\,{expr})"


def atempo_chain(speed):
    parts, s = [], speed
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    parts.append(f"atempo={s:.4f}")
    return ",".join(parts)


def clip_video(i, c, W, H, fps):
    speed = c.get("speed", 1)
    f = [f"[{i}:v]trim=start={c['in']}:end={c['out']},setpts=PTS-STARTPTS"]
    if speed != 1:
        f.append(f"setpts=PTS/{speed}")
    f.append(f"fps={fps}")
    fit = c.get("fit", "cover")
    if fit == "blur":  # video horizontal en vertical: fondo desenfocado + video completo
        body = ",".join(f)
        return (f"{body},split[bg{i}][fg{i}];"
                f"[bg{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:2,eq=brightness=-0.08[bgb{i}];"
                f"[fg{i}]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs{i}];"
                f"[bgb{i}][fgs{i}]overlay=(W-w)/2:(H-h)/2" + grade(c) + f",format=yuv420p,setsar=1[v{i}]")
    z = lerp_expr(c.get("zoom"), 1)
    cx = lerp_expr(c.get("x"), 0.5)
    cy = lerp_expr(c.get("y"), 0.5)
    f.append(f"scale=w='trunc(iw*max({W}/iw\\,{H}/ih)*({z})/2)*2':h=-2:eval=frame")
    f.append(f"crop={W}:{H}:x='clip(({cx})*iw-{W}/2\\,0\\,iw-{W})':y='clip(({cy})*ih-{H}/2\\,0\\,ih-{H})'")
    return ",".join(f) + grade(c) + f",format=yuv420p,setsar=1[v{i}]"


def grade(c):
    g = ""
    if c.get("lut"):
        g += f",lut3d=file='{esc(c['lut'])}'"
    if c.get("eq"):
        g += f",eq={c['eq']}"
    if c.get("vf"):  # cualquier filtro de ffmpeg: curves, colortemperature, vibrance, vignette…
        g += f",{c['vf']}"
    return g


def clip_audio(i, c, src_has_audio):
    d = (c["out"] - c["in"]) / c.get("speed", 1)
    if c.get("audio", True) and src_has_audio:
        a = f"[{i}:a]atrim=start={c['in']}:end={c['out']},asetpts=PTS-STARTPTS"
        if c.get("speed", 1) != 1:
            a += "," + atempo_chain(c["speed"])
        gain = c.get("gain", 0)
        return a + f",volume={gain}dB,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={d:.4f}[a{i}]"
    return f"anullsrc=r=48000:cl=stereo,atrim=duration={d:.4f}[a{i}]"


def build_base(spec, root, out):
    W, H = spec["size"]
    fps = spec.get("fps", 30)
    clips = spec["clips"]
    inputs, graph = [], []
    for i, c in enumerate(clips):
        src = root / c["src"]
        if src.suffix.lower() in IMAGES:  # una foto es un clip de (out - in) segundos
            inputs += ["-loop", "1", "-framerate", str(fps), "-t", str(c["out"])]
        inputs += ["-i", str(src)]
        if c.get("lut"):
            c = {**c, "lut": str(root / c["lut"])}
        graph.append(clip_video(i, c, W, H, fps))
        graph.append(clip_audio(i, c, has_audio(src)))

    durs = [(c["out"] - c["in"]) / c.get("speed", 1) for c in clips]
    v, a, total = "[v0]", "[a0]", durs[0]
    for k in range(1, len(clips)):
        tr = clips[k].get("transition")
        if tr:
            td = tr.get("dur", 0.3)
            off = total - td
            # concat y xfade dejan bases de tiempo distintas: se igualan antes de cada transición
            graph.append(f"{v}settb=AVTB,fps={fps}[pv{k}]")
            graph.append(f"[v{k}]settb=AVTB,fps={fps}[qv{k}]")
            graph.append(f"[pv{k}][qv{k}]xfade=transition={tr.get('type', 'fade')}:duration={td}:offset={off:.4f}[xv{k}]")
            graph.append(f"{a}[a{k}]acrossfade=d={td}[xa{k}]")
            total += durs[k] - td
        else:
            graph.append(f"{v}{a}[v{k}][a{k}]concat=n=2:v=1:a=1[xv{k}][xa{k}]")
            total += durs[k]
        v, a = f"[xv{k}]", f"[xa{k}]"

    return (["ffmpeg", "-v", "error", "-stats", "-y", *inputs, "-filter_complex", ";".join(graph),
             "-map", v, "-map", a, *encode(fps), str(out)], total)


def build_final(spec, root, out):
    W, H = spec["size"]
    fps = spec.get("fps", 30)
    base = root / spec["base"]
    dur = duration(base)
    inputs, graph = ["-i", str(base)], []
    n = 1
    v = "[0:v]"
    for k, L in enumerate(spec.get("layers", [])):
        src = root / L["src"]
        if src.suffix == ".webm":  # el decodificador nativo de VP9 ignora el alfa
            inputs += ["-c:v", "libvpx-vp9"]
        inputs += ["-i", str(src)]
        st = L.get("start", 0)
        chain = f"[{n}:v]setpts=PTS-STARTPTS+{st}/TB,format=yuva420p"
        if L.get("scale", True):
            chain += f",scale={W}:{H}"
        if L.get("vf"):  # p. ej. re-iluminar solo al sujeto recortado
            chain += f",{L['vf']}"
        if L.get("opacity", 1) != 1:
            chain += f",colorchannelmixer=aa={L['opacity']}"
        graph.append(chain + f"[l{k}]")
        graph.append(f"{v}[l{k}]overlay=0:0:eof_action=pass:format=auto[ov{k}]")
        v = f"[ov{k}]"
        n += 1

    mix, voices, music = [], [], []
    if has_audio(base) and spec.get("base_audio", True):
        graph.append(f"[0:a]volume={spec.get('base_gain', 0)}dB[ba]")
        mix.append("[ba]")
    for k, A in enumerate(spec.get("audio", [])):
        inputs += ["-i", str(root / A["src"])]
        ms = int(A.get("start", 0) * 1000)
        chain = f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo"
        if A.get("trim"):
            chain += f",atrim=start={A['trim'][0]}:end={A['trim'][1]},asetpts=PTS-STARTPTS"
        if A.get("fade_out"):
            chain += f",afade=t=out:st={dur - ms / 1000 - A['fade_out']:.3f}:d={A['fade_out']}"
        chain += f",volume={A.get('gain', 0)}dB,adelay={ms}|{ms}"
        graph.append(chain + f"[au{k}]")
        (music if A.get("role") == "music" else voices).append(f"[au{k}]")
        n += 1

    if voices and music and spec.get("duck", True):
        graph.append(f"{''.join(voices)}amix=inputs={len(voices)}:normalize=0,asplit[vo][key]" if len(voices) > 1
                     else f"{voices[0]}asplit[vo][key]")
        graph.append(f"{''.join(music)}amix=inputs={len(music)}:normalize=0[mu]" if len(music) > 1
                     else f"{music[0]}anull[mu]")
        graph.append("[mu][key]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350[mud]")
        mix += ["[vo]", "[mud]"]
    else:
        mix += voices + music

    amap = []
    if mix:
        lufs = spec.get("loudness", -14)
        graph.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=longest,"
                     f"apad,atrim=duration={dur:.4f},loudnorm=I={lufs}:TP=-1.0:LRA=11,aresample=48000[aout]")
        amap = ["-map", "[aout]"]
    graph.append(f"{v}format=yuv420p[vout]")
    return ["ffmpeg", "-v", "error", "-stats", "-y", *inputs, "-filter_complex", ";".join(graph),
            "-map", "[vout]", *amap, "-t", f"{dur:.4f}", *encode(fps), str(out)]


def encode(fps):
    return ["-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]


def export_otio(spec, root, path, final):
    import opentimelineio as otio

    fps = spec.get("fps", 30)
    rt = lambda s: otio.opentime.RationalTime(round(s * fps), fps)  # noqa: E731
    tl = otio.schema.Timeline(name=spec.get("name", "compas-studio"))
    v1 = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
    if final:  # para retoques: V1 es el base ya cortado y con color, y las capas calzan encima
        base = root / spec["base"]
        ref = otio.schema.ExternalReference(target_url=str(base.resolve()))
        v1.append(otio.schema.Clip(name=base.stem, media_reference=ref,
                                   source_range=otio.opentime.TimeRange(rt(0), rt(duration(base)))))
    else:  # etapa base: las tomas originales con sus in/out (sin zoom ni color)
        for c in spec.get("clips", []):
            ref = otio.schema.ExternalReference(target_url=str((root / c["src"]).resolve()))
            v1.append(otio.schema.Clip(name=Path(c["src"]).stem, media_reference=ref,
                                       source_range=otio.opentime.TimeRange(rt(c["in"]), rt(c["out"] - c["in"]))))
    tl.tracks.append(v1)
    if not final:
        otio.adapters.write_to_file(tl, str(path))
        return

    def placed(kind, name, items):
        tr = otio.schema.Track(name=name, kind=kind)
        for it in items:
            src = root / it["src"]
            st = it.get("start", 0)
            if st:
                tr.append(otio.schema.Gap(source_range=otio.opentime.TimeRange(rt(0), rt(st))))
            d = duration(src)
            ref = otio.schema.ExternalReference(target_url=str(src.resolve()))
            tr.append(otio.schema.Clip(name=src.stem, media_reference=ref,
                                       source_range=otio.opentime.TimeRange(rt(0), rt(d))))
        return tr

    for k, L in enumerate(spec.get("layers", [])):
        tl.tracks.append(placed(otio.schema.TrackKind.Video, Path(L["src"]).stem, [L]))

    # Audio: el sonido del base en su pista, y cada rol (voz, música, sfx) en las mínimas pistas sin solaparse.
    if spec.get("base_audio", True) and has_audio(root / spec["base"]):
        tl.tracks.append(placed(otio.schema.TrackKind.Audio, "base", [{"src": spec["base"]}]))
    for role in ("voice", "music", "sfx"):
        lanes = []  # [(fin, [items])]
        for A in sorted((x for x in spec.get("audio", []) if x.get("role", "sfx") == role), key=lambda x: x.get("start", 0)):
            st, d = A.get("start", 0), duration(root / A["src"])
            lane = next((l for l in lanes if l[0] <= st + 1e-6), None)
            if lane is None:
                lane = [0, []]
                lanes.append(lane)
            lane[1].append({**A, "start": st - lane[0]})
            lane[0] = st + d
        for n, (_, items) in enumerate(lanes):
            tl.tracks.append(placed(otio.schema.TrackKind.Audio, f"{role}{n + 1}", items))
    otio.adapters.write_to_file(tl, str(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--stage", choices=["base", "final"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--otio")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    spec_path = Path(a.spec).resolve()
    spec, root = json.loads(spec_path.read_text()), spec_path.parent

    if a.stage == "base":
        cmd, total = build_base(spec, root, a.out)
        print(f"base: {len(spec['clips'])} clips, {total:.2f}s")
    else:
        cmd = build_final(spec, root, a.out)
    if a.dry:
        print(shlex.join(cmd))
        return
    subprocess.run(cmd, check=True)
    if a.otio:
        export_otio(spec, root, a.otio, a.stage == "final")
        print(f"otio: {a.otio}")
    print(f"listo: {a.out} ({duration(a.out):.2f}s)")


if __name__ == "__main__":
    main()
