"""Nickia - estado dos jobs em memoria."""
import threading
import time
import uuid
from typing import Any, Dict, Optional

_JOBS: Dict[str, Dict[str, Any]] = {}
_LOCK = threading.Lock()


def new_job(sentences_total: int = 0) -> str:
    jid = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[jid] = {
            "id": jid,
            "status": "queued",
            "progress": 0,
            "sentences_total": sentences_total,
            "sentences_done": 0,
            "current_sentence": "",
            "started_at": time.time(),
            "finished_at": None,
            "result": None,
            "error": None,
            "cancel_requested": False,
        }
    return jid


def update(jid: str, **kwargs) -> None:
    with _LOCK:
        if jid in _JOBS:
            _JOBS[jid].update(kwargs)


def get(jid: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        j = _JOBS.get(jid)
        return dict(j) if j else None


def cleanup_old(max_age_s: int = 3600) -> None:
    now = time.time()
    with _LOCK:
        for jid in list(_JOBS.keys()):
            j = _JOBS[jid]
            if j["finished_at"] and (now - j["finished_at"]) > max_age_s:
                del _JOBS[jid]
