"""Motor Chatterbox Multilingual PT-BR."""
import os
from pathlib import Path
from typing import Optional

from config import (
    DEFAULT_CFG_WEIGHT,
    DEFAULT_EXAGGERATION,
    DEFAULT_LANGUAGE,
    DEFAULT_TEMPERATURE,
    NUM_THREADS,
)

os.environ.setdefault("OMP_NUM_THREADS", str(NUM_THREADS))
os.environ.setdefault("MKL_NUM_THREADS", str(NUM_THREADS))
os.environ.setdefault("OPENBLAS_NUM_THREADS", str(NUM_THREADS))

import torch

torch.set_num_threads(NUM_THREADS)
try:
    torch.set_num_interop_threads(NUM_THREADS)
except RuntimeError:
    pass

_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs.setdefault("map_location", torch.device("cpu"))
    return _original_load(*args, **kwargs)
torch.load = _patched_load

from engine.base import TTSEngine


class ChatterboxPTBR(TTSEngine):
    def __init__(self, device: Optional[str] = None):
        self._device = torch.device(device or "cpu")
        self._model = None

    @property
    def name(self) -> str:
        return "chatterbox-ptbr"

    def load(self) -> None:
        if self._model is not None:
            return
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        self._model = ChatterboxMultilingualTTS.from_pretrained(device=self._device)

    def generate(
        self,
        text: str,
        ref_audio: Path,
        output_path: Path,
        language: str = DEFAULT_LANGUAGE,
        exaggeration: float = DEFAULT_EXAGGERATION,
        cfg_weight: float = DEFAULT_CFG_WEIGHT,
        temperature: float = DEFAULT_TEMPERATURE,
        seed: Optional[int] = None,
    ) -> Path:
        if self._model is None:
            self.load()

        ref_audio = Path(ref_audio)
        if not ref_audio.exists():
            raise FileNotFoundError(f"Audio de referencia nao encontrado: {ref_audio}")

        # Seed para reprodutibilidade / variacao controlada
        if seed is not None:
            torch.manual_seed(int(seed))
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(int(seed))

        wav = self._model.generate(
            text,
            language_id=language,
            audio_prompt_path=str(ref_audio),
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            temperature=temperature,
        )

        sr = getattr(self._model, "sr", 24000)
        if wav.dim() == 1:
            wav = wav.unsqueeze(0)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import soundfile as sf
        sf.write(str(output_path), wav.squeeze(0).cpu().numpy(), sr)
        return output_path
