"""Converte WAV para MP3 via FFmpeg."""
import shutil
import subprocess
from pathlib import Path


def find_ffmpeg() -> str:
    """Encontra o ffmpeg no PATH. Levanta erro se nao achar."""
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError(
            "FFmpeg nao encontrado no PATH. Instale com: "
            "winget install --id Gyan.FFmpeg -e --source winget"
        )
    return path


def wav_to_mp3(wav_path: Path, mp3_path: Path = None, bitrate: str = "192k") -> Path:
    """Converte WAV para MP3. Se mp3_path for None, usa o mesmo nome."""
    wav_path = Path(wav_path)
    if not wav_path.exists():
        raise FileNotFoundError(f"WAV nao encontrado: {wav_path}")

    if mp3_path is None:
        mp3_path = wav_path.with_suffix(".mp3")
    mp3_path = Path(mp3_path)
    mp3_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", str(wav_path),
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        str(mp3_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg falhou (codigo {result.returncode}):\n{result.stderr[-800:]}"
        )
    return mp3_path
