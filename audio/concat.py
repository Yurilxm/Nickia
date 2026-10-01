"""Concatena multiplos WAVs com pausa entre eles."""
from pathlib import Path
from typing import List, Optional

import numpy as np
import soundfile as sf

from config import OUTPUT_SAMPLE_RATE, PAUSE_BETWEEN_SENTENCES_MS


def _load_mono(path: Path, target_sr: int) -> np.ndarray:
    data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != target_sr:
        # reamostragem linear simples (evita dependencia extra)
        n = int(round(len(data) * target_sr / sr))
        data = np.interp(
            np.linspace(0, len(data) - 1, n),
            np.arange(len(data)),
            data,
        ).astype(np.float32)
    return data


def concat_wavs(
    wav_paths: List[Path],
    output_path: Path,
    sample_rate: Optional[int] = None,
    pause_ms: Optional[int] = None,
) -> Path:
    """Junta WAVs em sequencia, inserindo pausa de silencio entre eles."""
    if not wav_paths:
        raise ValueError("Lista de WAVs vazia")

    sr = sample_rate or OUTPUT_SAMPLE_RATE
    pause = pause_ms if pause_ms is not None else PAUSE_BETWEEN_SENTENCES_MS
    pause_samples = int(sr * pause / 1000)
    silence = np.zeros(pause_samples, dtype=np.float32)

    blocos = []
    for i, p in enumerate(wav_paths):
        if i > 0:
            blocos.append(silence)
        blocos.append(_load_mono(Path(p), sr))

    audio = np.concatenate(blocos) if blocos else np.array([], dtype=np.float32)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, sr)
    return output_path
