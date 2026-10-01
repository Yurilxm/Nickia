// Aba "Gerar áudio".
import * as api from "./api.js";
import { $, showMsg, hideMsg, setProgress, escapeHtml, STAGE_LABEL } from "./ui.js";
import { modalAlert } from "./modal.js";

let currentJobId = null;
let lastBody = null;  // para reuso em "gerar outra versao"

export function init() {
  $("#btnAudio").addEventListener("click", () => onGenerate());
  $("#btnCancelAudio").addEventListener("click", onCancel);

  // Delegação: botão "Gerar outra versão" no resultado
  $("#resultAudio").addEventListener("click", (e) => {
    const t = e.target.closest("button[data-action='regen']");
    if (!t) return;
    const seed = Math.floor(Math.random() * 1000000);
    onGenerate({ ...(lastBody || {}), seed });
  });
}

async function onGenerate(override = null) {
  const text = override?.text ?? $("#text").value.trim();
  if (!text) {
    modalAlert("Falta o texto", "Escreva o que você quer que a Nickia fale antes de gerar.");
    return;
  }

  hideMsg($("#smsgAudio"));
  $("#resultAudio").className = "result";
  $("#resultAudio").innerHTML = "";
  $("#pboxAudio").classList.add("on");
  setProgress("Audio", 0, "Enviando...", "");
  $("#btnAudio").disabled = true;
  $("#btnCancelAudio").style.display = "block";

  const body = {
    text,
    name: override?.name ?? ($("#audioName").value.trim() || null),
    voice: override?.voice ?? ($("#voice").value || null),
    exaggeration: override?.exaggeration ?? parseFloat($("#exaggeration").value),
    cfg_weight: override?.cfg_weight ?? parseFloat($("#cfg_weight").value),
    temperature: override?.temperature ?? parseFloat($("#temperature").value),
    seed: override?.seed ?? null,
  };
  lastBody = body;

  try {
    const d = await api.startGenerate(body);
    currentJobId = d.job_id;
    await api.pollJob(d.job_id, onTick);
  } catch (e) {
    showMsg($("#smsgAudio"), "Erro: " + e.message, "err");
    $("#pboxAudio").classList.remove("on");
  } finally {
    $("#btnAudio").disabled = false;
    $("#btnCancelAudio").style.display = "none";
    currentJobId = null;
  }
}

function onTick(j) {
  setProgress("Audio", j.progress || 0, STAGE_LABEL[j.status] || j.status, j.current_sentence);

  if (j.status === "done") {
    setProgress("Audio", 100, "Pronto!", "");
    renderResult(j.result);
    window.dispatchEvent(new CustomEvent("nickia:history-updated"));
    return true;
  }
  if (j.status === "error") {
    showMsg($("#smsgAudio"), "Falhou: " + (j.error || "erro"), "err");
    return true;
  }
  if (j.status === "cancelled") {
    showMsg($("#smsgAudio"), "Geração cancelada.", "warn");
    $("#pboxAudio").classList.remove("on");
    return true;
  }
  return false;
}

function renderResult(res) {
  const el = $("#resultAudio");
  el.className = "result on";
  el.innerHTML = `
    <div class="meta">
      <span><i class="ri-time-line"></i> <b>${res.duration_s}s</b> de áudio</span>
      <span><i class="ri-flashlight-line"></i> gerado em <b>${res.elapsed_s}s</b></span>
      <span><i class="ri-file-list-3-line"></i> <b>${res.sentences.length}</b> frase(s)</span>
    </div>
    <audio controls autoplay src="${res.mp3_url}?t=${Date.now()}"></audio>
    <div class="actions">
      <a class="download-btn" href="${res.mp3_url}" download><i class="ri-download-2-line"></i> Baixar MP3</a>
      <a class="download-btn" href="${res.wav_url}" download><i class="ri-download-2-line"></i> Baixar WAV</a>
      <button class="ghost" data-action="regen" style="margin-left:auto">
        <i class="ri-refresh-line"></i> Gerar outra versão
      </button>
    </div>
    <details style="margin-top:14px">
      <summary>Ver frases geradas</summary>
      <ol style="font-size:13px;color:var(--muted);line-height:1.7;margin:8px 0 0 18px">
        ${res.sentences.map(s => `<li>${escapeHtml(s)}</li>`).join("")}
      </ol>
    </details>
  `;
}

async function onCancel() {
  if (!currentJobId) return;
  try {
    await api.cancelJob(currentJobId);
  } catch (e) {
    console.error(e);
  }
}
