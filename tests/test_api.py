"""Testes dos endpoints FastAPI."""
from pathlib import Path


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_voices_vazio(client):
    r = client.get("/voices")
    assert r.status_code == 200
    assert r.json() == {"voices": []}


def test_outputs_vazio(client):
    r = client.get("/outputs")
    assert r.status_code == 200
    assert r.json() == {"outputs": []}


def test_generate_texto_vazio(client):
    r = client.post("/generate", json={"text": ""})
    assert r.status_code == 422  # validacao pydantic


def test_generate_texto_muito_longo(client):
    r = client.post("/generate", json={"text": "x" * 6000})
    assert r.status_code == 422


def test_generate_cria_job(client):
    r = client.post("/generate", json={"text": "Ola mundo."})
    assert r.status_code == 200
    data = r.json()
    assert "job_id" in data


def test_job_status(client):
    r = client.post("/generate", json={"text": "Ola mundo."})
    jid = r.json()["job_id"]
    r2 = client.get(f"/jobs/{jid}")
    assert r2.status_code == 200
    assert r2.json()["id"] == jid


def test_job_inexistente(client):
    r = client.get("/jobs/naoExiste123")
    assert r.status_code == 404


def test_cancel_job(client):
    r = client.post("/generate", json={"text": "Ola mundo."})
    jid = r.json()["job_id"]
    r2 = client.post(f"/jobs/{jid}/cancel")
    assert r2.status_code == 200


def test_rename_output_inexistente(client):
    r = client.patch("/outputs/abc123", json={"name": "teste"})
    assert r.status_code == 404


def test_delete_output_inexistente(client):
    r = client.delete("/outputs/abc123")
    assert r.status_code == 200
    assert r.json()["removed"] == []


def test_output_id_invalido(client):
    """ID com chars fora do permitido deve retornar 400."""
    r = client.delete("/outputs/" + "a" * 50)  # > 40 chars
    assert r.status_code == 400

    r2 = client.delete("/outputs/test@output")  # @ nao permitido
    assert r2.status_code == 400


def test_output_traversal_bloqueado(client):
    """Tentativa de path traversal nunca deve expor arquivo do sistema."""
    # O roteador pode normalizar ou a app rejeita. Em qualquer caso, nao 200.
    for url in (
        "/outputs/../etc/passwd",
        "/outputs/..%2Fetc%2Fpasswd",
        "/outputs/%2E%2E%2Fetc%2Fpasswd",
    ):
        r = client.delete(url)
        assert r.status_code != 200, f"{url} retornou 200"
        assert r.status_code in (400, 404), f"{url} retornou {r.status_code}"


def test_waveform_id_invalido(client):
    r = client.get("/waveform/..%2Fetc%2Fpasswd")
    assert r.status_code in (400, 404)


def test_pronunciation_get(client):
    r = client.get("/pronunciation")
    assert r.status_code == 200
    assert "rules" in r.json()


def test_pronunciation_put(client):
    r = client.put("/pronunciation", json={
        "rules": [
            {"key": "leggings", "value": "leguins"},
            {"key": "sale", "value": "seil"},
        ]
    })
    assert r.status_code == 200
    assert r.json()["count"] == 2

    r2 = client.get("/pronunciation")
    rules = r2.json()["rules"]
    assert rules.get("leggings") == "leguins"
    assert rules.get("sale") == "seil"


def test_pronunciation_normaliza_chave(client):
    r = client.put("/pronunciation", json={
        "rules": [{"key": "  LEGGINGS  ", "value": "leguins"}]
    })
    assert r.status_code == 200
    r2 = client.get("/pronunciation")
    assert "leggings" in r2.json()["rules"]
