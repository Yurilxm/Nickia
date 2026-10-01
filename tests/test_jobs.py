"""Testes do modulo de jobs em memoria."""
from app import jobs


def test_new_e_get():
    jid = jobs.new_job(sentences_total=3)
    j = jobs.get(jid)
    assert j["id"] == jid
    assert j["status"] == "queued"
    assert j["progress"] == 0
    assert j["sentences_total"] == 3
    assert j["cancel_requested"] is False


def test_update():
    jid = jobs.new_job()
    jobs.update(jid, status="generating", progress=42)
    j = jobs.get(jid)
    assert j["status"] == "generating"
    assert j["progress"] == 42


def test_get_inexistente():
    assert jobs.get("naoExiste123") is None


def test_update_inexistente_nao_quebra():
    jobs.update("naoExiste123", status="erro")  # nao deve lancar


def test_cleanup_old():
    import time
    jid = jobs.new_job()
    jobs.update(jid, finished_at=time.time() - 7200)
    jobs.cleanup_old(max_age_s=3600)
    assert jobs.get(jid) is None
