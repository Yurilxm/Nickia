// Aba "Editar vídeo" com trilha visual + corte de áudio e vídeo.
import * as api from "./api.js";
import { $, showMsg, hideMsg, setProgress, STAGE_LABEL } from "./ui.js";
import { modalAlert } from "./modal.js";

let videoPreviewUrl = null;
let previewAudioEl = null;

const wf = {
  samples: null, duration: 0, trimStart: 0, trimEnd: 0,
  dragging: null, loadedJid: null, canvas: null, ctx: null, dpr: 1,
};

const vt = {
  duration: 0, trimStart: 0, trimEnd: 0,
  dragging: null, canvas: null, ctx: null, dpr: 1,
};

export function init() {
  const vidFileEl = $("#vidFile");
  if (vidFileEl) vidFileEl.addEventListener("change", onFileSelected);

  const vidVolEl = $("#vidVol");
  if (vidVolEl) {
    vidVolEl.addEventListener("input", (e) => {
      const lbl = $("#vidVolVal");
      if (lbl) lbl.textContent = e.target.value + "%";
      updateModeHint();
    });
  }

  const vidAudioEl = $("#vidAudio");
  if (vidAudioEl) vidAudioEl.addEventListener("change", onAudioChanged);

  const btnVideo = $("#btnVideo");
  if (btnVideo) btnVideo.addEventListener("click", onGenerate);

  const btnPreview = $("#btnPreviewTrim");
  if (btnPreview) btnPreview.addEventListener("click", previewTrim);

  document.querySelectorAll('input[name="vidmode"]').forEach(r => {
    r.addEventListener("change", updateModeHint);
  });

  wf.canvas = $("#waveformCanvas");
  if (wf.canvas) {
    wf.ctx = wf.canvas.getContext("2d");
    wf.dpr = window.devicePixelRatio || 1;
    wf.canvas.addEventListener("mousedown", onAudioDown);
    window.addEventListener("mousemove", onAudioMove);
    window.addEventListener("mouseup", () => { wf.dragging = null; });
  }

  vt.canvas = $("#videoTimelineCanvas");
  if (vt.canvas) {
    vt.ctx = vt.canvas.getContext("2d");
    vt.dpr = window.devicePixelRatio || 1;
    vt.canvas.addEventListener("mousedown", onVideoDown);
    window.addEventListener("mousemove", onVideoMove);
    window.addEventListener("mouseup", () => { vt.dragging = null; });
  }

  window.addEventListener("resize", () => {
    if (wf.samples) { resizeCanvas(wf, 80); drawWaveform(); }
    if (vt.duration > 0) { resizeCanvas(vt, 60); drawVideoTimeline(); }
  });

  window.addEventListener("nickia:audio-list-updated", () => {
    wf.loadedJid = null;
    onAudioChanged();
    updateModeHint();
  });

  setTimeout(onAudioChanged, 300);
  setTimeout(updateModeHint, 500);
}

// ---------- hint ----------
function currentMode() {
  const el = document.querySelector('input[name="vidmode"]:checked');
  return el ? el.value : "auto";
}

function updateModeHint() {
  const el = $("#modeHint");
  if (!el) return;

  const vDur = vt.duration || 0;
  const aDur = wf.duration ? (wf.trimEnd - wf.trimStart) : 0;

  if (!vDur || !aDur) {
    el.innerHTML = `<i class="ri-information-line"></i> Escolha um vídeo e uma narração para ver o resumo.`;
    el.classList.remove("warn");
    return;
  }

  const mode = currentMode();
  let html = "";
  let warn = false;

  if (mode === "auto") {
    if (aDur < vDur - 0.3) {
      const diff = (vDur - aDur).toFixed(1);
      html = `<i class="ri-information-line"></i> Áudio tem <b>${aDur.toFixed(1)}s</b>. Vídeo tem <b>${vDur.toFixed(1)}s</b>. Os últimos <b>${diff}s</b> do vídeo ficarão <b>em silêncio</b>.`;
    } else if (aDur > vDur + 0.3) {
      const diff = (aDur - vDur).toFixed(1);
      html = `<i class="ri-scissors-line"></i> Áudio tem <b>${aDur.toFixed(1)}s</b>. Vídeo tem <b>${vDur.toFixed(1)}s</b>. Os últimos <b>${diff}s</b> do áudio serão <b>cortados</b>.`;
      warn = true;
    } else {
      html = `<i class="ri-check-line"></i> Áudio e vídeo têm durações compatíveis (~<b>${aDur.toFixed(1)}s</b>).`;
    }
  } else if (mode === "loop") {
    const reps = vDur / aDur;
    if (reps < 1.05) {
      html = `<i class="ri-information-line"></i> Áudio já cobre o vídeo (${aDur.toFixed(1)}s ≥ ${vDur.toFixed(1)}s). Não haverá repetição.`;
    } else {
      html = `<i class="ri-repeat-line"></i> Áudio de <b>${aDur.toFixed(1)}s</b> será <b>repetido ${reps.toFixed(1)}×</b> para cobrir os <b>${vDur.toFixed(1)}s</b> do vídeo.`;
    }
  } else if (mode === "match_audio") {
    if (aDur > vDur + 0.3) {
      html = `<i class="ri-expand-height-line"></i> O vídeo de <b>${vDur.toFixed(1)}s</b> será <b>esticado/congelado</b> até os <b>${aDur.toFixed(1)}s</b> do áudio.`;
    } else {
      const diff = (vDur - aDur).toFixed(1);
      html = `<i class="ri-scissors-line"></i> O vídeo será <b>cortado</b> de <b>${vDur.toFixed(1)}s</b> para <b>${aDur.toFixed(1)}s</b> (perde ${diff}s).`;
    }
  }

  el.innerHTML = html;
  el.classList.toggle("warn", warn);
}

// ---------- audio waveform ----------
function currentAudioJid() {
  const v = $("#vidAudio")?.value;
  if (!v) return null;
  return v.replace(/\.wav$/, "");
}

function onFileSelected(e) {
  const f = e.target.files[0];
  if (!f) return;
  if (videoPreviewUrl) URL.revokeObjectURL(videoPreviewUrl);
  videoPreviewUrl = URL.createObjectURL(f);
  const v = $("#vidPreview");
  const wrap = $("#vidPreviewWrap");
  if (!v || !wrap) return;
  v.src = videoPreviewUrl;
  wrap.style.display = "block";
  v.addEventListener("loadedmetadata", () => {
    const dur = v.duration;
    const info = $("#vidInfo");
    if (info) info.innerHTML =
      `<i class="ri-information-line"></i> ${f.name} — ${dur.toFixed(1)}s — ${(f.size/1024/1024).toFixed(1)} MB`;

    vt.duration = dur;
    vt.trimStart = 0;
    vt.trimEnd = dur;
    const sec = $("#videoTimelineWrap");
    if (sec) sec.style.display = "block";
    requestAnimationFrame(() => requestAnimationFrame(() => {
      resizeCanvas(vt, 60);
      drawVideoTimeline();
    }));
    updateModeHint();
  }, { once: true });
}

async function onAudioChanged() {
  const jid = currentAudioJid();
  if (!jid) return;
  if (wf.loadedJid === jid) return;
  wf.loadedJid = jid;
  await loadWaveform(jid);
}

async function loadWaveform(jid) {
  if (!wf.canvas) return;
  try {
    const r = await fetch("/waveform/" + jid);
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    wf.samples = d.samples;
    wf.duration = d.duration;
    wf.trimStart = 0;
    wf.trimEnd = d.duration;
    const sec = $("#waveformSection");
    if (sec) sec.style.display = "block";
    requestAnimationFrame(() => requestAnimationFrame(() => {
      resizeCanvas(wf, 80);
      drawWaveform();
    }));
    updateModeHint();
  } catch (e) {
    console.error("waveform erro:", e);
  }
}

// ---------- canvas helpers ----------
function resizeCanvas(obj, h) {
  if (!obj.canvas) return;
  const wrap = obj.canvas.parentElement;
  const w = Math.max(200, wrap.clientWidth);
  obj.canvas.style.width = w + "px";
  obj.canvas.style.height = h + "px";
  obj.canvas.width = Math.round(w * obj.dpr);
  obj.canvas.height = Math.round(h * obj.dpr);
}

function drawHandles(ctx, W, H, startX, endX, dpr) {
  ctx.fillStyle = "#a78bfa";
  const gw = 6 * dpr;
  ctx.fillRect(startX - gw / 2, 0, gw, H);
  ctx.fillRect(endX - gw / 2, 0, gw, H);
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 1 * dpr;
  ctx.beginPath();
  ctx.moveTo(startX, H * 0.3); ctx.lineTo(startX, H * 0.7);
  ctx.moveTo(endX, H * 0.3); ctx.lineTo(endX, H * 0.7);
  ctx.stroke();
}

// ---------- audio ----------
function drawWaveform() {
  if (!wf.canvas || !wf.ctx) return;
  const ctx = wf.ctx;
  const W = wf.canvas.width, H = wf.canvas.height;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = "rgba(10,12,20,0.6)";
  ctx.fillRect(0, 0, W, H);
  if (!wf.samples || !wf.samples.length || wf.duration <= 0) return;

  const n = wf.samples.length, midY = H / 2;
  const startX = (wf.trimStart / wf.duration) * W;
  const endX = (wf.trimEnd / wf.duration) * W;
  const barW = W / n;
  for (let i = 0; i < n; i++) {
    const x = i * barW;
    const inSel = x >= startX && x <= endX;
    ctx.fillStyle = inSel ? "#a78bfa" : "rgba(139,143,163,0.35)";
    const barH = Math.max(2, wf.samples[i] * H * 0.85);
    ctx.fillRect(x, midY - barH / 2, Math.max(1, barW - 0.5), barH);
  }
  ctx.fillStyle = "rgba(10,12,20,0.55)";
  if (startX > 0) ctx.fillRect(0, 0, startX, H);
  if (endX < W) ctx.fillRect(endX, 0, W - endX, H);
  drawHandles(ctx, W, H, startX, endX, wf.dpr);

  const sl = $("#trimStartLabel"); if (sl) sl.textContent = wf.trimStart.toFixed(2) + "s";
  const el = $("#trimEndLabel");   if (el) el.textContent = wf.trimEnd.toFixed(2) + "s";
  const dl = $("#trimDuration");   if (dl) dl.textContent = Math.max(0, wf.trimEnd - wf.trimStart).toFixed(2) + "s";
}

function onAudioDown(e) {
  if (!wf.samples || !wf.canvas) return;
  const rect = wf.canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * wf.dpr;
  const W = wf.canvas.width;
  const sX = (wf.trimStart / wf.duration) * W;
  const eX = (wf.trimEnd / wf.duration) * W;
  const tol = 14 * wf.dpr;
  if (Math.abs(x - sX) <= tol) wf.dragging = "start";
  else if (Math.abs(x - eX) <= tol) wf.dragging = "end";
  else wf.dragging = Math.abs(x - sX) < Math.abs(x - eX) ? "start" : "end";
  e.preventDefault();
}

function onAudioMove(e) {
  if (!wf.dragging || !wf.canvas) return;
  const rect = wf.canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * wf.dpr;
  const W = wf.canvas.width;
  const t = Math.max(0, Math.min(wf.duration, (x / W) * wf.duration));
  const g = 0.1;
  if (wf.dragging === "start") wf.trimStart = Math.max(0, Math.min(t, wf.trimEnd - g));
  else wf.trimEnd = Math.min(wf.duration, Math.max(t, wf.trimStart + g));
  drawWaveform();
  updateModeHint();
}

// ---------- video timeline ----------
function drawVideoTimeline() {
  if (!vt.canvas || !vt.ctx) return;
  const ctx = vt.ctx;
  const W = vt.canvas.width, H = vt.canvas.height;
  ctx.clearRect(0, 0, W, H);
  if (vt.duration <= 0) return;

  ctx.fillStyle = "rgba(10,12,20,0.6)";
  ctx.fillRect(0, 0, W, H);

  const stripeW = 4 * vt.dpr;
  for (let x = 0; x < W; x += stripeW * 2) {
    ctx.fillStyle = "rgba(167,139,250,0.35)";
    ctx.fillRect(x, 0, stripeW, H);
  }

  const startX = (vt.trimStart / vt.duration) * W;
  const endX = (vt.trimEnd / vt.duration) * W;

  ctx.fillStyle = "rgba(10,12,20,0.7)";
  if (startX > 0) ctx.fillRect(0, 0, startX, H);
  if (endX < W) ctx.fillRect(endX, 0, W - endX, H);

  drawHandles(ctx, W, H, startX, endX, vt.dpr);

  const sl = $("#vTrimStartLabel"); if (sl) sl.textContent = vt.trimStart.toFixed(2) + "s";
  const el = $("#vTrimEndLabel");   if (el) el.textContent = vt.trimEnd.toFixed(2) + "s";
  const dl = $("#vTrimDuration");   if (dl) dl.textContent = Math.max(0, vt.trimEnd - vt.trimStart).toFixed(2) + "s";
}

function onVideoDown(e) {
  if (!vt.canvas || vt.duration <= 0) return;
  const rect = vt.canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * vt.dpr;
  const W = vt.canvas.width;
  const sX = (vt.trimStart / vt.duration) * W;
  const eX = (vt.trimEnd / vt.duration) * W;
  const tol = 14 * vt.dpr;
  if (Math.abs(x - sX) <= tol) vt.dragging = "start";
  else if (Math.abs(x - eX) <= tol) vt.dragging = "end";
  else vt.dragging = Math.abs(x - sX) < Math.abs(x - eX) ? "start" : "end";
  e.preventDefault();
}

function onVideoMove(e) {
  if (!vt.dragging || !vt.canvas) return;
  const rect = vt.canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * vt.dpr;
  const W = vt.canvas.width;
  const t = Math.max(0, Math.min(vt.duration, (x / W) * vt.duration));
  const g = 0.1;
  if (vt.dragging === "start") vt.trimStart = Math.max(0, Math.min(t, vt.trimEnd - g));
  else vt.trimEnd = Math.min(vt.duration, Math.max(t, vt.trimStart + g));
  drawVideoTimeline();
  updateModeHint();
}

function previewTrim() {
  const jid = currentAudioJid();
  if (!jid || !wf.samples) return;
  if (previewAudioEl) { previewAudioEl.pause(); previewAudioEl = null; }
  const a = new Audio(`/outputs/${jid}.wav?t=${Date.now()}`);
  previewAudioEl = a;
  const stopAt = wf.trimEnd;
  a.addEventListener("loadedmetadata", () => { a.currentTime = wf.trimStart; a.play(); }, { once: true });
  const check = () => {
    if (previewAudioEl !== a) return;
    if (a.currentTime >= stopAt) { a.pause(); previewAudioEl = null; return; }
    requestAnimationFrame(check);
  };
  requestAnimationFrame(check);
  a.addEventListener("ended", () => { previewAudioEl = null; });
}

async function onGenerate() {
  const f = $("#vidFile")?.files?.[0];
  if (!f) { modalAlert("Falta o vídeo", "Escolha o vídeo da loja que você quer montar."); return; }
  const audio = $("#vidAudio")?.value;
  if (!audio) { modalAlert("Falta a narração", "Gere uma narração na aba 'Gerar áudio' primeiro."); return; }

  hideMsg($("#smsgVideo"));
  $("#resultVideo").className = "result";
  $("#resultVideo").innerHTML = "";
  $("#pboxVideo").classList.add("on");
  setProgress("Video", 0, "Enviando vídeo...", "");
  $("#btnVideo").disabled = true;

  const mode = currentMode();
  const vol = parseFloat($("#vidVol").value) / 100;

  const fd = new FormData();
  fd.append("video", f);
  fd.append("audio", audio);
  fd.append("mode", mode);
  fd.append("original_volume", vol);
  fd.append("trim_start", wf.trimStart.toFixed(3));
  fd.append("trim_end", wf.trimEnd.toFixed(3));
  fd.append("video_trim_start", vt.trimStart.toFixed(3));
  fd.append("video_trim_end", vt.trimEnd.toFixed(3));

  try {
    const d = await api.startVideoCompose(fd);
    await api.pollJob(d.job_id, onTick);
  } catch (e) {
    showMsg($("#smsgVideo"), "Erro: " + e.message, "err");
    $("#pboxVideo").classList.remove("on");
  } finally {
    $("#btnVideo").disabled = false;
  }
}

function onTick(j) {
  setProgress("Video", j.progress || 0, STAGE_LABEL[j.status] || j.status);
  if (j.status === "done") {
    setProgress("Video", 100, "Pronto!", "");
    const res = j.result;
    $("#resultVideo").className = "result on";
    $("#resultVideo").innerHTML = `
      <div class="meta">
        <span><i class="ri-file-video-line"></i> <b>${res.size_mb} MB</b></span>
      </div>
      <video controls src="${res.video_url}?t=${Date.now()}"></video>
      <div class="actions">
        <a class="download-btn" href="${res.video_url}" download><i class="ri-download-2-line"></i> Baixar vídeo</a>
      </div>
    `;
    return true;
  }
  if (j.status === "error") {
    showMsg($("#smsgVideo"), "Falhou: " + (j.error || "erro"), "err");
    return true;
  }
  return false;
}
