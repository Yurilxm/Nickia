"""Testa a engine pela interface TTSEngine."""
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import DEFAULT_REF_AUDIO, OUTPUT_DIR
from engine.chatterbox_ptbr import ChatterboxPTBR


def main():
    ref = DEFAULT_REF_AUDIO
    if not ref.exists():
        print(f"[ERRO] Referencia nao encontrada: {ref}")
        sys.exit(1)

    texto_file = BASE_DIR / "data" / "texto.txt"
    texto = texto_file.read_text(encoding="utf-8").strip()
    print(f"Texto: {len(texto)} chars")
    print(f"Referencia: {ref.name}")

    engine = ChatterboxPTBR()
    print(f"Engine: {engine.name}")

    print("Carregando modelo...")
    t0 = time.time()
    engine.load()
    print(f"[OK] Load: {time.time()-t0:.1f} s")

    out = OUTPUT_DIR / "teste_engine_interface.wav"
    print("Gerando...")
    t0 = time.time()
    engine.generate(texto, ref_audio=ref, output_path=out)
    dt = time.time() - t0
    print(f"[OK] Geracao: {dt:.1f} s")
    print(f"[OK] Salvo: {out}")


if __name__ == "__main__":
    main()
