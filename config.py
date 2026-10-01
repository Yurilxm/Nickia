"""Nickia - configuracoes centrais."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
VOICES_DIR = DATA_DIR / "voices"
OUTPUT_DIR = DATA_DIR / "output"
WEB_DIR = BASE_DIR / "web"
MODELS_DIR = BASE_DIR / "models"

for _d in (DATA_DIR, VOICES_DIR, OUTPUT_DIR, WEB_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --- TTS ---
DEFAULT_LANGUAGE = "pt"
DEFAULT_EXAGGERATION = 0.5
DEFAULT_CFG_WEIGHT = 0.5
DEFAULT_TEMPERATURE = 0.8
DEFAULT_REPETITION_PENALTY = 2.0
DEFAULT_MIN_P = 0.05
DEFAULT_TOP_P = 1.0

# --- Texto ---
MAX_CHARS_PER_SENTENCE = 250

# --- Audio ---
OUTPUT_SAMPLE_RATE = 24000
PAUSE_BETWEEN_SENTENCES_MS = 350

# --- Threads (CPU) ---
NUM_THREADS = int(os.environ.get("NICKIA_THREADS", os.cpu_count() or 4))

# --- Caminho do audio de referencia padrao ---
DEFAULT_REF_AUDIO = VOICES_DIR / "nickia_ref01_short.wav"
