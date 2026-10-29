"""Mapa de profundidad de una imagen (Depth Anything V2), para el parallax 2.5D de templates/parallax.html.

Uso: ~/.venvs/studio/bin/python -I depth.py <imagen> <salida_depth.png> [--model small|base]
Blanco = cerca, negro = lejos.
"""
import argparse
from pathlib import Path

import torch
from PIL import Image
from transformers import pipeline

ap = argparse.ArgumentParser()
ap.add_argument("image")
ap.add_argument("out")
ap.add_argument("--model", default="small", choices=["small", "base"])
a = ap.parse_args()

import sys
sys.path.insert(0, str(Path(__file__).parent))
from equipo import device

dev = device()
pipe = pipeline("depth-estimation", model=f"depth-anything/Depth-Anything-V2-{a.model.capitalize()}-hf", device=dev)
im = Image.open(a.image).convert("RGB")
d = pipe(im)["depth"].resize(im.size, Image.BICUBIC)
d.save(a.out)
print(f"listo: {a.out} {im.size}")
