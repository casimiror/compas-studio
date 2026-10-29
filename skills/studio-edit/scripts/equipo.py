"""Perfil del equipo: qué puede correr este computador y qué motor usa cada paso.

Uso: python -I equipo.py            → revisa el equipo, escribe ~/.config/compas-studio/equipo.json y muestra el plan
     STUDIO_DEVICE=cpu python ...   → simula un equipo sin GPU (para probar los motores de respaldo)

Los otros scripts importan `perfil()` y `device()` para escoger motor sin que nadie tenga que configurarlo.
Niveles:
  mac-mlx   Mac con Apple Silicon: MLX (whisper y SAM 2.1 rápidos), torch en MPS.
  cuda      PC o servidor con GPU NVIDIA: faster-whisper y torch en CUDA. SAM 2.1 MLX no corre: máscaras con YOLO.
  cpu       Cualquier otro (laptop sin GPU, servidor barato): faster-whisper int8 con modelo chico, YOLO en CPU (lento),
            sin SAM 2.1; voz clonada lenta (mejor generarla en otro equipo o con un servicio).
"""
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

CONF = Path.home() / ".config/compas-studio/equipo.json"


def _ram_gb():
    try:
        if platform.system() == "Darwin":
            return round(int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout) / 2**30)
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30)
    except Exception:
        return None


def _has(mod):
    import importlib.util
    return importlib.util.find_spec(mod) is not None


def perfil():
    forced = os.environ.get("STUDIO_DEVICE")
    apple = platform.system() == "Darwin" and platform.machine() == "arm64"
    cuda = mps = False
    try:
        import torch
        cuda = torch.cuda.is_available()
        mps = torch.backends.mps.is_available()
    except Exception:
        pass
    accel = forced or ("cuda" if cuda else "mps" if mps else "cpu")
    nivel = "mac-mlx" if accel == "mps" and apple else "cuda" if accel == "cuda" else "cpu"
    sam_py = Path.home() / ".venvs/sam-mlx/bin/python"
    return {
        "sistema": f"{platform.system()} {platform.machine()}",
        "ram_gb": _ram_gb(),
        "acelerador": accel,
        "nivel": nivel,
        "whisper": "mlx" if nivel == "mac-mlx" and _has("mlx_whisper") else ("faster-whisper" if _has("faster_whisper") else None),
        "whisper_modelo": os.environ.get("STUDIO_WHISPER_MODEL") or ("large-v3-turbo" if nivel != "cpu" else "small"),
        "sam2": nivel == "mac-mlx" and sam_py.exists(),
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "node": shutil.which("node") is not None,
    }


def device():
    """Dispositivo de torch: cuda, mps o cpu (respeta STUDIO_DEVICE)."""
    return perfil()["acelerador"]


PLAN = {
    "mac-mlx": {"transcribir": "mlx-whisper large-v3-turbo (~1 s por cada 10 s de voz)", "máscaras": "SAM 2.1 MLX o YOLO en MPS",
                "voz clonada": "Chatterbox en MPS (~40 s por frase)", "render": "Chromium + ffmpeg"},
    "cuda": {"transcribir": "faster-whisper large-v3-turbo en CUDA", "máscaras": "YOLO en CUDA (SAM 2.1 MLX no corre)",
             "voz clonada": "Chatterbox en CUDA", "render": "Chromium + ffmpeg"},
    "cpu": {"transcribir": "faster-whisper small int8 en CPU (más lento, algo menos preciso)",
            "máscaras": "YOLO en CPU (lento: usar clips cortos) o sin máscara", "voz clonada": "no recomendada en CPU: generar en otro equipo o usar la voz real",
            "render": "Chromium + ffmpeg (funciona igual)"},
}

# Si el equipo no puede con un paso: qué hacer sin él y qué servicios externos lo hacen.
# Los servicios piden cuenta y llave (la configura el usuario, nunca el agente) y casi todos cobran: se usan solo con su aprobación.
ALTERNATIVAS = {
    "voz clonada": ["usar la voz real (grabar la frase con el celular)",
                    "generar el .wav en un equipo mac-mlx o cuda y copiarlo",
                    "ElevenLabs (clonación de voz, API; pago)", "Resemble AI (los creadores de Chatterbox, API; pago)",
                    "voz sin clonar: OpenAI TTS, Google Cloud TTS o Azure Speech (pago por uso)"],
    "transcripción": ["faster-whisper con modelo small en CPU (ya incluido; más lento)",
                      "OpenAI (Whisper / gpt-4o-transcribe), Deepgram, AssemblyAI o Groq (API; pago por minuto)",
                      "subtítulos automáticos de CapCut o de Instagram (gratis, a mano)"],
    "máscaras": ["evitar el efecto: texto encima en vez de detrás de la persona",
                 "YOLO en CPU sobre un clip corto (2–4 s)",
                 "SAM 2 alojado en Replicate o fal.ai (API; pago por uso)",
                 "quitar fondo en CapCut o Runway (a mano)"],
    "equipo con GPU": ["Google Colab, RunPod o Modal: alquilar GPU por horas para un lote pesado (pago)"],
}
FALTA = {"mac-mlx": [], "cuda": ["máscaras"], "cpu": ["voz clonada", "transcripción", "máscaras", "equipo con GPU"]}

if __name__ == "__main__":
    p = perfil()
    CONF.parent.mkdir(parents=True, exist_ok=True)
    CONF.write_text(json.dumps(p, indent=2, ensure_ascii=False))
    print(json.dumps(p, indent=2, ensure_ascii=False))
    print(f"\nPlan para este equipo ({p['nivel']}):")
    for k, v in PLAN[p["nivel"]].items():
        print(f"  {k:12} {v}")
    faltan = [n for n, ok in [("ffmpeg", p["ffmpeg"]), ("node", p["node"]), ("whisper (mlx-whisper o faster-whisper)", p["whisper"])] if not ok]
    if faltan:
        print("\nFalta instalar:", ", ".join(faltan))
    lim = FALTA[p["nivel"]]
    if lim:
        print("\nLímites de este equipo y alternativas (servicios externos: con cuenta y aprobación del usuario):")
        for k in lim:
            print(f"  {k}:")
            for alt in ALTERNATIVAS[k]:
                print(f"    - {alt}")
