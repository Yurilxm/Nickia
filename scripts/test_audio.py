"""Testa concat + mp3 usando WAVs ja gerados."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import OUTPUT_DIR
from audio.concat import concat_wavs
from audio.convert import wav_to_mp3


def main():
    # Pega os 2 WAVs mais recentes que existem
    todos = sorted(
        OUTPUT_DIR.glob("*.wav"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    wavs = todos[:2]
    if len(wavs) < 2:
        print(f"[ERRO] Preciso de 2 WAVs em {OUTPUT_DIR}. Achei {len(wavs)}.")
        for p in todos:
            print(f"  - {p.name}")
        sys.exit(1)

    print("Concat:")
    for p in wavs:
        print(f"  - {p.name} ({p.stat().st_size/1024:.0f} KB)")
    out_wav = OUTPUT_DIR / "teste_concat.wav"
    concat_wavs(wavs, out_wav, pause_ms=500)
    print(f"[OK] {out_wav}")

    import soundfile as sf
    data, sr = sf.read(str(out_wav))
    print(f"     Duracao: {len(data)/sr:.1f} s @ {sr} Hz")

    print("Convertendo para MP3...")
    out_mp3 = wav_to_mp3(out_wav, bitrate="192k")
    print(f"[OK] {out_mp3}")
    print(f"     Tamanho: {out_mp3.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
