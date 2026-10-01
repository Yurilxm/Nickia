"""Testes de concat e conversao de audio."""
import numpy as np
import soundfile as sf
import pytest

from audio.concat import concat_wavs
from audio.convert import wav_to_mp3, find_ffmpeg


def _make_wav(path, sr=24000, dur=1.0, freq=440):
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    sig = (0.3 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    sf.write(str(path), sig, sr)
    return path


def test_concat_duracao(tmp_path):
    a = _make_wav(tmp_path / "a.wav", dur=1.0)
    b = _make_wav(tmp_path / "b.wav", dur=2.0, freq=880)
    out = concat_wavs([a, b], tmp_path / "out.wav", pause_ms=500)
    data, sr = sf.read(str(out))
    # 1s + 0.5s pausa + 2s = 3.5s (+/- tolerancia)
    assert abs(len(data) / sr - 3.5) < 0.05


def test_concat_lista_vazia(tmp_path):
    with pytest.raises(ValueError):
        concat_wavs([], tmp_path / "out.wav")


def test_mp3(tmp_path):
    try:
        find_ffmpeg()
    except RuntimeError:
        pytest.skip("FFmpeg nao disponivel")
    wav = _make_wav(tmp_path / "in.wav", dur=1.0)
    mp3 = wav_to_mp3(wav)
    assert mp3.exists()
    assert mp3.stat().st_size > 0
    assert mp3.suffix == ".mp3"
