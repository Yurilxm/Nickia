"""Fixtures compartilhadas dos testes."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))


@pytest.fixture
def tmp_outputs(monkeypatch, tmp_path):
    """Redireciona OUTPUT_DIR/VOICES_DIR para uma pasta temporaria."""
    import config
    out = tmp_path / "output"
    voices = tmp_path / "voices"
    out.mkdir()
    voices.mkdir()
    monkeypatch.setattr(config, "OUTPUT_DIR", out)
    monkeypatch.setattr(config, "VOICES_DIR", voices)
    return out, voices


@pytest.fixture
def client(tmp_outputs):
    """Cliente FastAPI com config isolada."""
    from fastapi.testclient import TestClient
    # reimporta o app para pegar a nova config
    import importlib
    import app.main as main_mod
    importlib.reload(main_mod)
    return TestClient(main_mod.app)
