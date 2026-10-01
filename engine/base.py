"""Interface abstrata do motor TTS."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class TTSEngine(ABC):
    """Contrato que qualquer motor de voz deve cumprir."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do motor (ex.: 'chatterbox-ptbr')."""

    @abstractmethod
    def load(self) -> None:
        """Carrega o modelo. Idempotente."""

    @abstractmethod
    def generate(
        self,
        text: str,
        ref_audio: Path,
        output_path: Path,
        language: str = "pt",
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5,
        temperature: float = 0.8,
    ) -> Path:
        """Gera audio e salva em output_path. Retorna o caminho."""
