"""Testes do endpoint /waveform (contrato consumido pelo preview)."""
import numpy as np
import soundfile as sf
import pytest


@pytest.fixture
def wav_no_outputs(client, tmp_outputs):
    """Cria um WAV no OUTPUT_DIR isolado e retorna o jid."""
    out_dir, _ = tmp_outputs
    jid = "testwave01"
    sr = 24000
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    sig = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    sf.write(str(out_dir / f"{jid}.wav"), sig, sr)
    return jid


def test_waveform_retorna_estrutura(client, wav_no_outputs):
    r = client.get(f"/waveform/{wav_no_outputs}")
    assert r.status_code == 200
    d = r.json()
    assert "samples" in d
    assert "duration" in d
    assert "sample_rate" in d


def test_waveform_samples_sao_lista(client, wav_no_outputs):
    r = client.get(f"/waveform/{wav_no_outputs}")
    d = r.json()
    assert isinstance(d["samples"], list)
    assert len(d["samples"]) > 100


def test_waveform_samples_entre_0_e_1(client, wav_no_outputs):
    r = client.get(f"/waveform/{wav_no_outputs}")
    d = r.json()
    for s in d["samples"]:
        assert 0.0 <= s <= 1.0, f"sample fora do range: {s}"


def test_waveform_duracao_correta(client, wav_no_outputs):
    r = client.get(f"/waveform/{wav_no_outputs}")
    d = r.json()
    assert abs(d["duration"] - 2.0) < 0.05
    assert d["sample_rate"] == 24000


def test_waveform_id_invalido(client):
    r = client.get("/waveform/..%2Fetc%2Fpasswd")
    assert r.status_code in (400, 404)


def test_waveform_inexistente(client):
    r = client.get("/waveform/naoExiste123")
    assert r.status_code == 404
