"""SAM 2.1 en MLX (mlx-sam): sigue un objeto por todo el video y escribe una máscara PNG por frame en resolución original.

Lo llama mask.py --engine sam2; corre en su propio entorno porque mlx-sam exige Python 3.14:
  ~/.venvs/sam-mlx/bin/python -I sam_mlx.py <video> <masks_dir> (--box x0,y0,x1,y1 | --point x,y[;x,y…]) [--frame N] [--size 512]

--size es la resolución interna del modelo (512 ≈ 0,1 s/frame en un M1 Pro, 1024 ≈ 0,65 s/frame); la máscara sale
siempre al tamaño del video. Con --frame > 0 propaga hacia adelante y hacia atrás desde ese frame.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from mlx_sam import SAM2VideoPredictor

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("masks")
ap.add_argument("--box")
ap.add_argument("--point")
ap.add_argument("--frame", type=int, default=0)
ap.add_argument("--size", type=int, default=512)
ap.add_argument("--model", default="avbiswas/sam2.1-hiera-small-mlx")
a = ap.parse_args()

out = Path(a.masks)
out.mkdir(parents=True, exist_ok=True)
p = SAM2VideoPredictor.from_pretrained(a.model, image_size=a.size, memory_dtype="float16",
                                       memory_attention_dtype="float16")
st = p.init_state(a.video)
kw = {}
if a.box:
    kw["box"] = np.array([float(v) for v in a.box.split(",")], np.float32)
if a.point:
    pts = [[float(v) for v in pt.split(",")] for pt in a.point.split(";")]
    kw["points"] = np.array(pts, np.float32)
    kw["labels"] = np.ones(len(pts), np.int32)
p.add_new_points_or_box(st, frame_idx=a.frame, obj_id=1, **kw)

passes = [False] if a.frame == 0 else [False, True]
for rev in passes:
    for fi, _ids, m in p.propagate_in_video(st, start_frame_idx=a.frame, reverse=rev):
        cv2.imwrite(str(out / f"{fi + 1:05d}.png"), (m[0, 0] > 0).astype(np.uint8) * 255)
print(f"sam_mlx: {len(list(out.glob('*.png')))} máscaras en {out}")
