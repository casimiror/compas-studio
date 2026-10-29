"""Segmenta un sujeto en cada frame: máscara, recorte con alfa y seguimiento (para que el JS lo siga).

Uso: ~/.venvs/studio/bin/python -I mask.py <video> <carpeta_salida> [opciones]

Motores:
  --engine yolo   (por defecto) personas u objetos COCO, rápido. --classes 0 = persona; 39 botella; 41 taza…
  --engine sam2   SAM 2.1 en MLX: el mejor seguimiento, cualquier objeto. Prompt: caja automática de YOLO (--classes),
                  --box x0,y0,x1,y1 o --point x,y, sobre el frame --frame N. ~0,1 s/frame a --size 512.
  --engine rembg  BiRefNet frame a frame: el mejor borde de persona/producto, el más lento (~1 s/frame).

Salida: masks/00001.png…, subject.mov (ProRes 4444: el sujeto con alfa), track.json
  track.json = {fps, w, h, frames: [{t, box: [x, y, w, h] | null, cx, cy}]}
"""
import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

MODELS = Path.home() / ".cache" / "studio-models"  # pesos de YOLO y SAM, fuera de la carpeta de trabajo


def fps_of(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return fps, n, w, h


def frames(path):
    cap = cv2.VideoCapture(str(path))
    while True:
        ok, f = cap.read()
        if not ok:
            break
        yield f
    cap.release()


def masks_yolo(path, classes, w, h):
    from ultralytics import YOLO

    model = YOLO(str(MODELS / "yolo11m-seg.pt"))
    main_id = None
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from equipo import device

    dev = device()
    for r in model.track(source=str(path), stream=True, classes=classes, persist=True, verbose=False,
                         retina_masks=True, device=dev, save=False):
        m = np.zeros((h, w), np.uint8)
        if r.masks is not None and len(r.masks):
            ids = r.boxes.id.int().tolist() if r.boxes.id is not None else list(range(len(r.masks)))
            areas = r.boxes.xywh[:, 2] * r.boxes.xywh[:, 3]
            if main_id not in ids:  # el sujeto principal: el más grande la primera vez que aparece
                main_id = ids[int(areas.argmax())]
            i = ids.index(main_id)
            data = r.masks.data[i].cpu().numpy()
            m = (cv2.resize(data, (w, h)) > 0.5).astype(np.uint8) * 255
        yield m


def yolo_box(path, frame_idx, classes):
    """Caja del objeto más grande de esas clases en un frame: el prompt para SAM (un clic suelto es ambiguo)."""
    from ultralytics import YOLO

    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ok, f = cap.read()
    cap.release()
    r = YOLO(str(MODELS / "yolo11m.pt"))(f, classes=classes, verbose=False)[0]
    if not len(r.boxes):
        raise SystemExit(f"sam2: YOLO no encontró clases {classes} en el frame {frame_idx}; pasa --box o --point")
    b = r.boxes.xyxy[int((r.boxes.xywh[:, 2] * r.boxes.xywh[:, 3]).argmax())].tolist()
    return ",".join(f"{v:.0f}" for v in b)


def masks_sam2(path, mdir, a, n, w, h):
    # mlx-sam (MLX, Python 3.14) en su propio entorno: ~0,1 s/frame a --size 512, con la máscara en resolución original.
    box = a.box or (None if a.point else yolo_box(path, a.frame, [int(c) for c in a.classes.split(",")]))
    cmd = [str(Path.home() / ".venvs/sam-mlx/bin/python"), "-I", str(Path(__file__).with_name("sam_mlx.py")),
           str(path), str(mdir), "--frame", str(a.frame), "--size", str(a.size)]
    cmd += ["--box", box] if box else ["--point", a.point]
    print("sam2:", "caja " + box if box else "puntos " + a.point, flush=True)
    subprocess.run(cmd, check=True)
    for i in range(n):
        m = cv2.imread(str(mdir / f"{i + 1:05d}.png"), 0)
        yield m if m is not None else np.zeros((h, w), np.uint8)


def masks_rembg(path, model):
    from PIL import Image
    from rembg import new_session, remove

    sess = new_session(model)
    for f in frames(path):
        im = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        yield np.array(remove(im, session=sess, only_mask=True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--engine", choices=["yolo", "sam2", "rembg"], default="yolo")
    ap.add_argument("--classes", default="0", help="yolo: clases COCO separadas por coma")
    ap.add_argument("--point", help="sam2: x,y[;x,y…] en píxeles del video (mejor --box o la caja automática)")
    ap.add_argument("--box", help="sam2: x0,y0,x1,y1 en píxeles del video. Sin --box ni --point, YOLO pone la caja (--classes)")
    ap.add_argument("--frame", type=int, default=0, help="sam2: frame donde se marca el objeto (propaga a ambos lados)")
    ap.add_argument("--size", type=int, default=512, help="sam2: resolución interna (512 rápido; 1024 si el borde falla)")
    ap.add_argument("--rembg-model", default="birefnet-portrait", help="birefnet-portrait | birefnet-general")
    ap.add_argument("--feather", type=float, default=1.5, help="desenfoque del borde de la máscara (px)")
    ap.add_argument("--no-mov", action="store_true")
    a = ap.parse_args()

    out = Path(a.out)
    mdir = out / "masks"
    mdir.mkdir(parents=True, exist_ok=True)
    fps, n, w, h = fps_of(a.video)

    if a.engine == "sam2":
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from equipo import perfil

        if not perfil()["sam2"]:
            print("mask: SAM 2.1 (MLX) solo corre en Mac con Apple Silicon; en este equipo uso YOLO", flush=True)
            a.engine = "yolo"
    if a.engine == "yolo":
        gen = masks_yolo(a.video, [int(c) for c in a.classes.split(",")], w, h)
    elif a.engine == "sam2":
        gen = masks_sam2(a.video, mdir, a, n, w, h)
    else:
        gen = masks_rembg(a.video, a.rembg_model)

    track = []
    for i, m in enumerate(gen):
        cv2.imwrite(str(mdir / f"{i + 1:05d}.png"), m)
        ys, xs = np.where(m > 127)
        if len(xs):
            x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            track.append({"t": round(i / fps, 3), "box": [x0, y0, x1 - x0, y1 - y0],
                          "cx": int(xs.mean()), "cy": int(ys.mean()), "top": y0})
        else:
            track.append({"t": round(i / fps, 3), "box": None})
        if i % 30 == 0:
            print(f"frame {i}/{n}", flush=True)

    (out / "track.json").write_text(json.dumps({"fps": fps, "w": w, "h": h, "frames": track}))

    if not a.no_mov:
        blur = f",gblur=sigma={a.feather}" if a.feather > 0 else ""
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", a.video, "-framerate", str(fps), "-i", str(mdir / "%05d.png"),
            "-filter_complex", f"[1:v]format=gray{blur}[m];[0:v][m]alphamerge,format=yuva444p10le",
            "-an", "-c:v", "prores_ks", "-profile:v", "4444", str(out / "subject.mov"),
        ], check=True)
    vis = sum(1 for f in track if f["box"])
    mov = "" if a.no_mov else f"{out}/subject.mov, "
    print(f"listo: {len(track)} frames, sujeto visible en {vis}. {mov}{out}/track.json")


if __name__ == "__main__":
    main()
