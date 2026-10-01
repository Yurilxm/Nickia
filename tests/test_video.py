"""Testes do compose de video (usa ffmpeg para gerar entrada)."""
import shutil
import subprocess

import numpy as np
import soundfile as sf
import pytest

from audio.video import compose, get_duration, has_audio_stream


def _ffmpeg_ok():
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


pytestmark = pytest.mark.skipif(not _ffmpeg_ok(), reason="FFmpeg indisponivel")


def _make_test_video(path, dur=3.0):
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=blue:s=320x240:d={dur}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-shortest", "-pix_fmt", "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return path


def _make_test_audio(path, dur=2.0, sr=24000):
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    sig = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    sf.write(str(path), sig, sr)
    return path


def test_get_duration(tmp_path):
    v = _make_test_video(tmp_path / "v.mp4", dur=2.0)
    d = get_duration(v)
    assert abs(d - 2.0) < 0.2


def test_has_audio(tmp_path):
    v = _make_test_video(tmp_path / "v.mp4", dur=1.0)
    assert has_audio_stream(v)


def test_compose_auto(tmp_path):
    v = _make_test_video(tmp_path / "v.mp4", dur=2.0)
    a = _make_test_audio(tmp_path / "a.wav", dur=1.0)
    out = compose(v, a, tmp_path / "out.mp4", mode="auto", original_volume=0.0)
    assert out.exists()
    assert out.stat().st_size > 0


def test_compose_loop(tmp_path):
    v = _make_test_video(tmp_path / "v.mp4", dur=4.0)
    a = _make_test_audio(tmp_path / "a.wav", dur=1.0)
    out = compose(v, a, tmp_path / "out.mp4", mode="loop", original_volume=0.0)
    assert out.exists()


def test_compose_match_audio(tmp_path):
    v = _make_test_video(tmp_path / "v.mp4", dur=1.0)
    a = _make_test_audio(tmp_path / "a.wav", dur=3.0)
    out = compose(v, a, tmp_path / "out.mp4", mode="match_audio", original_volume=0.0)
    assert out.exists()
    dur = get_duration(out)
    assert dur > 2.5  # deve ter alongado


def test_compose_audio_trim(tmp_path):
    """Audio normal com audio curto: video continua com silencio no fim.
    Saida = duracao do video (5s), nao do audio (1s)."""
    v = _make_test_video(tmp_path / "v.mp4", dur=5.0)
    a = _make_test_audio(tmp_path / "a.wav", dur=4.0)
    out = compose(v, a, tmp_path / "out.mp4", mode="auto",
                  original_volume=0.0, trim_start=1.0, trim_end=2.0)
    assert out.exists()
    dur = get_duration(out)
    # video = 5s, audio = 1s, saida deve ser ~5s com silencio no fim
    assert 4.5 < dur < 5.5


def test_compose_video_trim(tmp_path):
    """Corte do video de 5s para 2s (1.0 ate 3.0)."""
    v = _make_test_video(tmp_path / "v.mp4", dur=5.0)
    a = _make_test_audio(tmp_path / "a.wav", dur=5.0)
    out = compose(v, a, tmp_path / "out.mp4", mode="auto",
                  original_volume=0.0, video_trim_start=1.0, video_trim_end=3.0)
    assert out.exists()
    dur = get_duration(out)
    assert 1.5 < dur < 3.5


def test_compose_modo_invalido(tmp_path):
    v = _make_test_video(tmp_path / "v.mp4", dur=1.0)
    a = _make_test_audio(tmp_path / "a.wav", dur=1.0)
    with pytest.raises(ValueError):
        compose(v, a, tmp_path / "out.mp4", mode="invalido")


def test_compose_volume_invalido(tmp_path):
    v = _make_test_video(tmp_path / "v.mp4", dur=1.0)
    a = _make_test_audio(tmp_path / "a.wav", dur=1.0)
    with pytest.raises(ValueError):
        compose(v, a, tmp_path / "out.mp4", mode="auto", original_volume=1.5)
