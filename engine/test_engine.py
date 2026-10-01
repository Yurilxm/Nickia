"""Nickia - teste de velocidade com N threads configuravel."""
import os
import sys
import time
from pathlib import Path

# Threads vem do argumento da linha de comando, ou usa cpu_count
if len(sys.argv) > 1:
    _n = int(sys.argv[1])
else:
    _n = os.cpu_count() or 4

os.environ["OMP_NUM_THREADS"] = str(_n)
os.environ["MKL_NUM_THREADS"] = str(_n)
os.environ["OPENBLAS_NUM_THREADS"] = str(_n)

import torch
torch.set_num_threads(_n)
try:
    torch.set_num_interop_threads(_n)
except RuntimeError:
    pass

# Monkeypatch torch.load -> cpu
_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs.setdefault("map_location", torch.device("cpu"))
    return _original_load(*args, **kwargs)
torch.load = _patched_load

BASE_DIR = Path(__file__).resolve().parent.parent
REF_AUDIO = BASE_DIR / "data" / "voices" / "nickia_ref01_short.wav"
TEXT_FILE = BASE_DIR / "data" / "texto.txt"
OUT_DIR = BASE_DIR / "data" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / f"teste_nickia_{_n}threads.wav"


def main():
    print(f"Threads: {_n}")
    print(f"Referencia: {REF_AUDIO.name}")

    texto = TEXT_FILE.read_text(encoding="utf-8").strip()
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    device = torch.device("cpu")
    print("Carregando modelo...")
    t0 = time.time()
    model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    t_load = time.time() - t0
    print(f"[OK] Carregado em {t_load:.1f} s")

    print("Gerando audio...")
    t0 = time.time()
    wav = model.generate(
        texto,
        language_id="pt",
        audio_prompt_path=str(REF_AUDIO),
    )
    t_gen = time.time() - t0
    print(f"[OK] Geracao: {t_gen:.1f} s")

    sr = getattr(model, "sr", 24000)
    if wav.dim() == 1:
        wav = wav.unsqueeze(0)
    dur = wav.shape[-1] / sr

    import soundfile as sf
    sf.write(str(OUT_FILE), wav.squeeze(0).cpu().numpy(), sr)

    print(f"[OK] Salvo: {OUT_FILE.name}")
    print(f"     Duracao: {dur:.1f} s")
    print(f"     TEMPO DE GERACAO: {t_gen:.1f} s")
    print(f"     FATOR: {t_gen/dur:.1f}x tempo-real")


if __name__ == "__main__":
    main()
