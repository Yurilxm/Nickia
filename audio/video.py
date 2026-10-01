"""Montagem de video com narracao (via FFmpeg)."""
import shutil
import subprocess
from pathlib import Path


def _ffmpeg() -> str:
    p = shutil.which("ffmpeg")
    if not p:
        raise RuntimeError("FFmpeg nao encontrado no PATH")
    return p


def _ffprobe() -> str:
    p = shutil.which("ffprobe")
    if not p:
        raise RuntimeError("FFprobe nao encontrado no PATH")
    return p


def get_duration(path) -> float:
    cmd = [_ffprobe(), "-v", "error",
           "-show_entries", "format=duration",
           "-of", "default=nw=1:nk=1", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe falhou: {r.stderr[-400:]}")
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def has_audio_stream(path) -> bool:
    cmd = [_ffprobe(), "-v", "error",
           "-select_streams", "a",
           "-show_entries", "stream=index",
           "-of", "csv=p=0", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0 and bool(r.stdout.strip())


def _trim_audio(audio_in: Path, t_start: float, t_end: float, tmp_dir: Path) -> Path:
    ffmpeg = _ffmpeg()
    output = tmp_dir / f"trim_{audio_in.stem}.wav"
    filt = f"atrim=start={t_start}:end={t_end},asetpts=PTS-STARTPTS"
    cmd = [ffmpeg, "-y", "-i", str(audio_in),
           "-af", filt, "-c:a", "pcm_s16le", str(output)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Trim audio falhou:\n{r.stderr[-800:]}")
    return output


def _trim_video(video_in: Path, t_start: float, t_end: float, tmp_dir: Path) -> Path:
    """Corta video com reencode (corte exato)."""
    ffmpeg = _ffmpeg()
    output = tmp_dir / f"trim_{video_in.stem}.mp4"
    dur = max(0.05, t_end - t_start)
    # -ss antes do -i e mais rapido; reencode garante corte exato
    cmd = [
        ffmpeg, "-y",
        "-ss", str(round(t_start, 3)),
        "-i", str(video_in),
        "-t", str(round(dur, 3)),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Trim video falhou:\n{r.stderr[-800:]}")
    return output


def compose(
    video_in: Path,
    audio_in: Path,
    output: Path,
    mode: str = "auto",
    original_volume: float = 0.0,
    trim_start: float = 0.0,
    trim_end: float = -1.0,
    video_trim_start: float = 0.0,
    video_trim_end: float = -1.0,
) -> Path:
    video_in = Path(video_in)
    audio_in = Path(audio_in)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if not video_in.exists():
        raise FileNotFoundError(f"Video nao encontrado: {video_in}")
    if not audio_in.exists():
        raise FileNotFoundError(f"Audio nao encontrado: {audio_in}")
    if mode not in ("auto", "loop", "match_audio"):
        raise ValueError(f"Modo invalido: {mode}")
    if not (0.0 <= original_volume <= 1.0):
        raise ValueError("original_volume deve estar entre 0 e 1")

    v_dur_full = get_duration(video_in)
    a_dur_full = get_duration(audio_in)
    has_oa = has_audio_stream(video_in)

    # ----- audio trim -----
    ts = max(0.0, float(trim_start))
    te = float(trim_end) if trim_end and trim_end > 0 else a_dur_full
    te = min(te, a_dur_full)
    if te <= ts:
        ts, te = 0.0, a_dur_full
    needs_audio_trim = (ts > 0.01) or (te < a_dur_full - 0.01)

    # ----- video trim -----
    vts = max(0.0, float(video_trim_start))
    vte = float(video_trim_end) if video_trim_end and video_trim_end > 0 else v_dur_full
    vte = min(vte, v_dur_full)
    if vte <= vts:
        vts, vte = 0.0, v_dur_full
    needs_video_trim = (vts > 0.01) or (vte < v_dur_full - 0.01)

    tmp_dir = output.parent / f"_trim_{output.stem}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Aplica trims em arquivos temporarios (2 passes isolados)
        video_effective = video_in
        if needs_video_trim:
            video_effective = _trim_video(video_in, vts, vte, tmp_dir)

        audio_effective = audio_in
        if needs_audio_trim:
            audio_effective = _trim_audio(audio_in, ts, te, tmp_dir)

        a_dur = get_duration(audio_effective)
        v_dur = get_duration(video_effective)

        # ----- compose -----
        filters = []
        if mode == "match_audio" and a_dur > v_dur:
            extra = round(a_dur - v_dur + 0.2, 3)
            filters.append(f"[0:v]tpad=stop_mode=clone:stop_duration={extra}[vout]")
            v_label = "[vout]"
            video_codec = ["-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "23", "-pix_fmt", "yuv420p"]
        else:
            v_label = "0:v"
            video_codec = ["-c:v", "copy"]

        orig_label = None
        if original_volume > 0.0 and has_oa:
            filters.append(f"[0:a:0]volume={original_volume}[oa]")
            orig_label = "[oa]"

        if mode in ("auto", "loop"):
            filters.append("[1:a]apad[na]")
        else:
            filters.append("[1:a]anull[na]")

        if orig_label:
            filters.append(
                f"{orig_label}[na]amix=inputs=2:duration=longest:dropout_transition=0[aout]"
            )
            a_label = "[aout]"
        else:
            a_label = "[na]"

        fc = ";".join(filters)

        cmd = [_ffmpeg(), "-y", "-i", str(video_effective)]
        if mode == "loop":
            cmd += ["-stream_loop", "-1"]
        cmd += ["-i", str(audio_effective)]
        cmd += ["-filter_complex", fc]
        cmd += ["-map", v_label, "-map", a_label]
        cmd += video_codec
        cmd += ["-c:a", "aac", "-b:a", "192k"]
        cmd += ["-shortest", "-movflags", "+faststart"]
        cmd += [str(output)]

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"FFmpeg falhou:\n{r.stderr[-1500:]}")
        return output
    finally:
        if tmp_dir.exists():
            for f in tmp_dir.iterdir():
                f.unlink(missing_ok=True)
            tmp_dir.rmdir()
