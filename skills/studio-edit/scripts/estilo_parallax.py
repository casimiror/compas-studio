"""Anima una imagen fija (2.5D): fondo y sujeto en capas separadas con parallax, aura que palpita,
líneas de velocidad, partículas y temblor de impacto. Uso: ~/.venvs/studio/bin/python -I estilo_parallax.py img.png mask.png bg.png out.mp4 [segundos]"""
import sys, subprocess, numpy as np, cv2
img, msk, bgp, out = sys.argv[1:5]; dur = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
W, H, FPS = 1080, 1920, 30
fg = cv2.imread(img).astype(np.float32); bg = cv2.imread(bgp).astype(np.float32)
a = cv2.imread(msk, 0).astype(np.float32) / 255
rng = np.random.default_rng(7)
P = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 6), rng.uniform(250, 600)) for _ in range(70)]
ang = rng.uniform(0, 2 * np.pi, 90)
def warp(x, s, dx, dy, ax, ay):  # escala s alrededor de (ax, ay) + desplazamiento
    M = np.float32([[s, 0, ax - s * ax + dx], [0, s, ay - s * ay + dy]])
    return cv2.warpAffine(x, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                      "-i", "-", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
N = int(dur * FPS)
for i in range(N):
    t = i / FPS; u = i / (N - 1); e = 1 - (1 - u) ** 2
    sh = 14 * np.exp(-t * 6) * np.sin(t * 90)  # temblor de impacto al inicio
    b = warp(bg, 1.06 + 0.03 * e, -25 * e + sh, 0, W / 2, H / 2)
    s_fg = 1.04 + 0.09 * e  # el sujeto se acerca más rápido que el fondo: parallax
    f = warp(fg, s_fg, 20 * e + sh, -30 * e, W / 2, H * 0.92)
    al = warp(a, s_fg, 20 * e + sh, -30 * e, W / 2, H * 0.92)[..., None]
    # líneas de velocidad radiales detrás del sujeto
    lines = np.zeros((H, W), np.float32); cx, cy = W / 2, H * 0.4
    for k, th in enumerate(ang):
        if (i + k) % 3: continue
        r0 = 380 + 200 * ((i * 7 + k * 13) % 10) / 10
        cv2.line(lines, (int(cx + r0 * np.cos(th)), int(cy + r0 * np.sin(th))),
                 (int(cx + 1500 * np.cos(th)), int(cy + 1500 * np.sin(th))), 1.0, 2 + k % 3)
    b = b * (1 - 0.55 * lines[..., None]) + 255 * 0.55 * lines[..., None]
    # aura: halo morado del contorno que palpita
    pulse = 0.65 + 0.35 * np.sin(t * 14) ** 2
    glow = cv2.GaussianBlur(cv2.dilate(al[..., 0], np.ones((25, 25), np.uint8)), (0, 0), 28) * pulse
    aura = np.dstack([255 * glow, 60 * glow, 200 * glow])
    b = np.clip(b + aura * 1.3, 0, 255)
    fr = f * al + b * (1 - al)
    # partículas subiendo
    for (x, y, rad, sp) in P:
        yy = (y - sp * t) % H; c = (255, 170, 240)
        cv2.circle(fr, (int(x + 15 * np.sin(t * 3 + x)), int(yy)), int(rad), c, -1, cv2.LINE_AA)
    if i < 3: fr = fr * 0.3 + 255 * 0.7  # flash de entrada
    p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait(); print("listo", out)
