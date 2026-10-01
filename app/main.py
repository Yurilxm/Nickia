"""Nickia - backend FastAPI (v0.3, limpo)."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import List, Optional

import numpy as np
from unidecode import unidecode

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    DEFAULT_CFG_WEIGHT,
    DEFAULT_EXAGGERATION,
    DEFAULT_LANGUAGE,
    DEFAULT_REF_AUDIO,
    DEFAULT_TEMPERATURE,
    MAX_CHARS_PER_SENTENCE,
    OUTPUT_DIR,
    PAUSE_BETWEEN_SENTENCES_MS,
    VOICES_DIR,
    WEB_DIR,
)
from engine.chatterbox_ptbr import ChatterboxPTBR
from text import normalize as text_normalize
from text import pronunciation, split
from audio.concat import concat_wavs
from audio.convert import wav_to_mp3
from audio.video import compose as video_compose
from app import jobs

app = FastAPI(title="Nickia", version="0.3.0")

_static_dir = WEB_DIR / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

_engine = ChatterboxPTBR()
_engine_loaded = False
_engine_lock = threading.Lock()

_VALID_VIDEO_MODES = {"auto", "loop", "match_audio"}
_SAFE_NAME = re.compile(r"[^a-zA-Z0-9_\-]+")
_SAFE_ID = re.compile(r"[a-zA-Z0-9_\-]{1,40}")

_INDEX_PATH = OUTPUT_DIR / "index.json"
_index_lock = threading.Lock()


def _ensure_engine_loaded():
    global _engine_loaded
    with _engine_lock:
        if not _engine_loaded:
            _engine.load()
            _engine_loaded = True


def _load_index() -> dict:
    if not _INDEX_PATH.exists():
        return {}
    try:
        return json.loads(_INDEX_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _save_index(idx: dict):
    _INDEX_PATH.write_text(
        json.dumps(idx, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _set_name(jid: str, name: str):
    with _index_lock:
        idx = _load_index()
        if jid in idx:
            idx[jid]["name"] = name
        else:
            idx[jid] = {"name": name, "created_at": int(time.time())}
        _save_index(idx)


def _should_cancel(jid: str) -> bool:
    j = jobs.get(jid)
    return bool(j and j.get("cancel_requested"))


def _slugify(name: str) -> str:
    nome = Path(name).stem
    nome = unidecode(nome)
    nome = _SAFE_NAME.sub("_", nome).strip("_")
    return nome or "voz"


# ==================== modelos ====================

class GenerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    name: Optional[str] = Field(None, max_length=60)
    voice: Optional[str] = None
    exaggeration: float = DEFAULT_EXAGGERATION
    cfg_weight: float = DEFAULT_CFG_WEIGHT
    temperature: float = DEFAULT_TEMPERATURE
    seed: Optional[int] = None


class GenerateResponse(BaseModel):
    job_id: str


class RenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)


# ==================== health / vozes ====================

@app.get("/health")
def health():
    return {"status": "ok", "engine_loaded": _engine_loaded}


@app.get("/voices")
def list_voices():
    return {"voices": sorted(p.name for p in VOICES_DIR.glob("*.wav"))}


# ==================== gerar audio ====================

def _run_job(jid: str, req: GenerateRequest):
    import threading as _th
    stop_ticker = _th.Event()

    def _ticker():
        # Atualiza progresso estimado a cada 1s
        while not stop_ticker.is_set():
            j = jobs.get(jid)
            if not j:
                return
            if j.get("status") not in ("generating",):
                stop_ticker.wait(1.0)
                continue

            state = j.get("_timing") or {}
            started = state.get("started_at")
            est_total = state.get("est_total_s") or 0
            base = state.get("base_progress", 8)
            span = state.get("span_progress", 80)
            if started and est_total > 0:
                elapsed = time.time() - started
                frac = min(1.0, elapsed / est_total)
                pct = base + span * frac
                jobs.update(jid, progress=int(pct))
            stop_ticker.wait(1.0)

    ticker = _th.Thread(target=_ticker, daemon=True)
    ticker.start()

    try:
        jobs.update(jid, status="loading", progress=2)
        _ensure_engine_loaded()
        jobs.update(jid, status="preparing", progress=6)

        texto = text_normalize.normalize(req.text)
        texto = pronunciation.apply(texto)
        frases = split.split_sentences(texto, MAX_CHARS_PER_SENTENCE)
        if not frases:
            raise ValueError("Texto vazio apos normalizacao")

        jobs.update(jid, sentences_total=len(frases))

        ref = VOICES_DIR / req.voice if req.voice else DEFAULT_REF_AUDIO
        if not ref.exists():
            raise FileNotFoundError(f"Voz nao encontrada: {ref.name}")

        tmp_dir = OUTPUT_DIR / f"_job_{jid}"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        wavs = []
        t0 = time.time()
        n = len(frases)
        chars_total = sum(len(f) for f in frases) or 1
        chars_done = 0

        for i, frase in enumerate(frases):
            if _should_cancel(jid):
                raise RuntimeError("Cancelado pela usuaria")

            # estimativa de tempo: baseada nas frases ja geradas
            if i == 0:
                # estimativa inicial conservadora: 15 chars/s
                cps = 15.0
            else:
                cps = chars_done / max(0.1, time.time() - t0)
                if cps < 1:
                    cps = 15.0

            chars_frase = len(frase)
            est_frase = chars_frase / max(1.0, cps)

            base = 8 + int(80 * (chars_done / chars_total))
            span = int(80 * (chars_frase / chars_total))

            jobs.update(
                jid,
                status="generating",
                current_sentence=frase,
                sentences_done=i,
                progress=base,
                _timing={
                    "started_at": time.time(),
                    "est_total_s": est_frase,
                    "base_progress": base,
                    "span_progress": span,
                },
            )

            p = tmp_dir / f"frase_{i:03d}.wav"
            _engine.generate(
                frase,
                ref_audio=ref,
                output_path=p,
                language=DEFAULT_LANGUAGE,
                exaggeration=req.exaggeration,
                cfg_weight=req.cfg_weight,
                temperature=req.temperature,
                seed=getattr(req, "seed", None),
            )
            wavs.append(p)
            chars_done += chars_frase

        jobs.update(
            jid,
            sentences_done=n,
            status="concatenating",
            progress=90,
            current_sentence="",
        )

        final_wav = OUTPUT_DIR / f"{jid}.wav"
        concat_wavs(wavs, final_wav, pause_ms=PAUSE_BETWEEN_SENTENCES_MS)

        jobs.update(jid, status="converting", progress=96)
        final_mp3 = wav_to_mp3(final_wav)

        for p in wavs:
            p.unlink(missing_ok=True)
        tmp_dir.rmdir()

        elapsed = time.time() - t0
        import soundfile as sf
        info = sf.info(str(final_wav))
        dur = info.frames / info.samplerate

        nome = (req.name or "").strip() or jid[:8]
        _set_name(jid, nome)

        with _index_lock:
            idx = _load_index()
            if jid not in idx:
                idx[jid] = {}
            idx[jid].update({
                "text": req.text,
                "voice": req.voice,
                "exaggeration": req.exaggeration,
                "cfg_weight": req.cfg_weight,
                "temperature": req.temperature,
                "name": nome,
            })
            _save_index(idx)

        jobs.update(
            jid,
            status="done",
            progress=100,
            finished_at=time.time(),
            result={
                "id": jid,
                "name": nome,
                "wav_url": f"/outputs/{final_wav.name}",
                "mp3_url": f"/outputs/{final_mp3.name}",
                "sentences": frases,
                "duration_s": round(dur, 2),
                "elapsed_s": round(elapsed, 1),
            },
        )
        jobs.cleanup_old()
    except Exception as e:
        is_cancel = "Cancelado" in str(e)
        jobs.update(
            jid,
            status="cancelled" if is_cancel else "error",
            error=None if is_cancel else str(e),
            finished_at=time.time(),
        )
    finally:
        stop_ticker.set()


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    jid = jobs.new_job()
    threading.Thread(target=_run_job, args=(jid, req), daemon=True).start()
    return GenerateResponse(job_id=jid)


@app.get("/jobs/{jid}")
def job_status(jid: str):
    j = jobs.get(jid)
    if not j:
        raise HTTPException(404, "Job nao encontrado")
    return j


@app.post("/jobs/{jid}/cancel")
def cancel_job(jid: str):
    j = jobs.get(jid)
    if not j:
        raise HTTPException(404, "Job nao encontrado")
    if j["status"] in ("done", "error", "cancelled"):
        return {"ok": False, "reason": "job ja finalizado"}
    jobs.update(jid, cancel_requested=True)
    return {"ok": True}


# ==================== outputs ====================

@app.get("/outputs")
def list_outputs(limit: int = 30):
    idx = _load_index()
    arquivos = sorted(
        OUTPUT_DIR.glob("*.wav"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]
    itens = []
    for p in arquivos:
        mp3 = p.with_suffix(".mp3")
        if not mp3.exists():
            continue
        meta = idx.get(p.stem, {})
        itens.append({
            "id": p.stem,
            "name": meta.get("name", p.stem[:8]),
            "wav": f"/outputs/{p.name}",
            "mp3": f"/outputs/{mp3.name}",
            "size_kb": round(p.stat().st_size / 1024),
            "mtime": int(p.stat().st_mtime),
        })
    return {"outputs": itens}


@app.patch("/outputs/{jid}")
def rename_output(jid: str, req: RenameRequest):
    if not _SAFE_ID.fullmatch(jid):
        raise HTTPException(400, "ID invalido")
    if not (OUTPUT_DIR / f"{jid}.wav").exists():
        raise HTTPException(404, "Audio nao encontrado")
    nome = req.name.strip()
    _set_name(jid, nome)
    return {"ok": True, "id": jid, "name": nome}


@app.delete("/outputs/{job_id}")
def delete_output(job_id: str):
    if not _SAFE_ID.fullmatch(job_id):
        raise HTTPException(400, "ID invalido")
    removidos = []
    for ext in (".wav", ".mp3"):
        p = OUTPUT_DIR / f"{job_id}{ext}"
        if p.exists():
            p.unlink()
            removidos.append(p.name)
    return {"ok": True, "removed": removidos}


@app.get("/outputs/{filename}")
def get_output(filename: str):
    base = OUTPUT_DIR.resolve()
    p = (OUTPUT_DIR / filename).resolve()
    if base != p.parent:
        raise HTTPException(403, "Caminho invalido")
    if not p.exists():
        raise HTTPException(404, "Arquivo nao encontrado")
    return FileResponse(str(p))


# ==================== upload de voz ====================

@app.post("/voices/upload")
async def upload_voice(
    name: str = Form(..., min_length=1, max_length=40),
    file: UploadFile = File(...),
):
    slug = _slugify(name)
    tmp_dir = Path(tempfile.mkdtemp(prefix="nickia_upload_"))
    tmp_in = tmp_dir / (file.filename or "entrada")
    try:
        with tmp_in.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        destino = VOICES_DIR / f"{slug}.wav"
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise HTTPException(500, "FFmpeg nao encontrado no PATH do servidor")

        cmd = [
            ffmpeg, "-y",
            "-i", str(tmp_in),
            "-ar", "16000", "-ac", "1",
            "-c:a", "pcm_s16le",
            str(destino),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise HTTPException(400, f"FFmpeg falhou: {r.stderr[-500:]}")

        return {
            "ok": True,
            "voice": destino.name,
            "size_kb": round(destino.stat().st_size / 1024),
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ==================== video ====================

def _run_video_job(jid, video_path, audio_path, mode, original_volume, tmp_dir,
                   trim_start=0.0, trim_end=-1.0,
                   video_trim_start=0.0, video_trim_end=-1.0):
    try:
        jobs.update(jid, status="preparing", progress=10)
        output_path = OUTPUT_DIR / f"{jid}.mp4"
        jobs.update(jid, status="generating", progress=30)

        video_compose(
            video_path, audio_path, output_path,
            mode=mode, original_volume=original_volume,
            trim_start=trim_start, trim_end=trim_end,
            video_trim_start=video_trim_start, video_trim_end=video_trim_end,
        )

        size_mb = round(output_path.stat().st_size / (1024 * 1024), 1)
        jobs.update(
            jid,
            status="done",
            progress=100,
            finished_at=time.time(),
            result={
                "id": jid,
                "video_url": f"/outputs/{output_path.name}",
                "size_mb": size_mb,
            },
        )
        jobs.cleanup_old()
    except Exception as e:
        jobs.update(jid, status="error", error=str(e), finished_at=time.time())
    finally:
        try:
            if tmp_dir.exists():
                for p in tmp_dir.iterdir():
                    p.unlink(missing_ok=True)
                tmp_dir.rmdir()
        except Exception:
            pass


@app.post("/video/compose")
async def video_compose_endpoint(
    video: UploadFile = File(...),
    audio: str = Form(...),
    mode: str = Form("auto"),
    original_volume: float = Form(0.0),
    trim_start: float = Form(0.0),
    trim_end: float = Form(-1.0),
    video_trim_start: float = Form(0.0),
    video_trim_end: float = Form(-1.0),
):
    if mode not in _VALID_VIDEO_MODES:
        raise HTTPException(400, f"Modo invalido: {mode}")
    if not (0.0 <= original_volume <= 1.0):
        raise HTTPException(400, "original_volume deve estar entre 0 e 1")
    if trim_start < 0:
        raise HTTPException(400, "trim_start nao pode ser negativo")
    if trim_end > 0 and trim_end <= trim_start:
        raise HTTPException(400, "trim_end deve ser maior que trim_start")
    if "/" in audio or "\\" in audio or ".." in audio:
        raise HTTPException(400, "Nome de audio invalido")

    audio_path = OUTPUT_DIR / audio
    if not audio_path.exists() or audio_path.suffix.lower() not in (".wav", ".mp3"):
        raise HTTPException(400, f"Audio nao encontrado: {audio}")

    tmp_dir = Path(tempfile.mkdtemp(prefix="nickia_video_"))
    ext = Path(video.filename or "video.mp4").suffix or ".mp4"
    video_path = tmp_dir / f"input{ext}"
    with video_path.open("wb") as f:
        shutil.copyfileobj(video.file, f)

    jid = jobs.new_job()
    threading.Thread(
        target=_run_video_job,
        args=(jid, video_path, audio_path, mode, original_volume, tmp_dir,
              trim_start, trim_end, video_trim_start, video_trim_end),
        daemon=True,
    ).start()
    return {"job_id": jid}


# ==================== waveform ====================

@app.get("/waveform/{jid}")
def waveform(jid: str):
    if not _SAFE_ID.fullmatch(jid):
        raise HTTPException(400, "ID invalido")
    wav_path = OUTPUT_DIR / f"{jid}.wav"
    if not wav_path.exists():
        raise HTTPException(404, "Audio nao encontrado")

    import soundfile as sf
    data, sr = sf.read(str(wav_path), dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)

    duration = len(data) / sr if sr else 0.0
    n_bars = 1500
    if len(data) == 0:
        return {"samples": [], "duration": 0.0, "sample_rate": sr}

    bucket = max(1, len(data) // n_bars)
    n_actual = len(data) // bucket
    trimmed = data[:n_actual * bucket].reshape(n_actual, bucket)
    peaks = np.abs(trimmed).max(axis=1)
    mx = float(peaks.max()) if peaks.size else 1.0
    if mx > 0:
        peaks = peaks / mx

    return {
        "samples": [round(float(x), 4) for x in peaks],
        "duration": round(duration, 3),
        "sample_rate": sr,
    }


# ==================== paginas ====================

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = WEB_DIR / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>Nickia</h1><p>web/index.html ainda nao criado.</p>")
    return HTMLResponse(html_path.read_text(encoding="utf-8-sig"))


# ============ Dicionario de pronuncia (B) ============

class PronRule(BaseModel):
    key: str = Field(..., min_length=1, max_length=60)
    value: str = Field(..., min_length=1, max_length=60)


class PronRules(BaseModel):
    rules: List[PronRule]


@app.get("/pronunciation")
def get_pronunciation():
    return {"rules": pronunciation.load_rules()}


@app.put("/pronunciation")
def put_pronunciation(body: PronRules):
    rules = {}
    for r in body.rules:
        k = r.key.strip().lower()
        v = r.value.strip()
        if k and v:
            rules[k] = v
    pronunciation.save_rules(rules)
    return {"ok": True, "count": len(rules)}
