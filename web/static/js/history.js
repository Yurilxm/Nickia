// Historico de narracoes + cadastro de vozes.
import * as api from "./api.js";
import { $, showMsg, escapeHtml } from "./ui.js";
import { modalAlert, modalConfirm, modalPrompt } from "./modal.js";

export function init() {
  $("#refreshHistory").addEventListener("click", refresh);
  $("#vbtn").addEventListener("click", onUploadVoice);
  window.addEventListener("nickia:history-updated", refresh);
  refresh();
}

export async function refresh() {
  const box = $("#history");
  box.innerHTML = '<div style="color:var(--muted);font-size:13px">Carregando...</div>';
  try {
    const d = await api.getOutputs();

    const asel = $("#vidAudio");
    const prevA = asel.value;
    asel.innerHTML = "";
    if (!d.outputs.length) {
      asel.innerHTML = '<option value="">(nenhuma narração ainda)</option>';
    } else {
      for (const it of d.outputs) {
        const o = document.createElement("option");
        o.value = it.id + ".wav";
        o.textContent = `${it.name} — ${it.id.slice(0,6)} (${it.size_kb} KB)`;
        asel.appendChild(o);
      }
      // preserva selecao; se nao tinha, seleciona o mais recente
      if (prevA && d.outputs.some(x => x.id + ".wav" === prevA)) {
        asel.value = prevA;
      } else {
        asel.value = d.outputs[0].id + ".wav";
      }
    }

    // avisa o video.js
    window.dispatchEvent(new CustomEvent("nickia:audio-list-updated"));

    if (!d.outputs.length) {
      box.innerHTML = '<div style="color:var(--muted);font-size:13px">Nada ainda. Gere sua primeira narração acima.</div>';
      return;
    }
    box.innerHTML = d.outputs.map(it => `
      <div class="history-item" data-id="${it.id}">
        <div class="top">
          <div class="left">
            <span class="fname" title="${escapeHtml(it.name)}">${escapeHtml(it.name)}</span>
            <span class="fid">#${it.id.slice(0,6)}</span>
            <span>${it.size_kb} KB</span>
          </div>
          <button class="iconbtn" onclick="window.__nickiaRename('${it.id}')" title="Renomear">
            <i class="ri-edit-line"></i> Renomear
          </button>
          <button class="danger" onclick="window.__nickiaDelete('${it.id}')" title="Excluir">
            <i class="ri-delete-bin-line"></i> Excluir
          </button>
        </div>
        <audio controls preload="none" src="${it.mp3}"></audio>
        <div class="actions">
          <a class="download-btn" href="${it.mp3}" download><i class="ri-download-2-line"></i> Baixar MP3</a>
          <a class="download-btn" href="${it.wav}" download><i class="ri-download-2-line"></i> Baixar WAV</a>
        </div>
      </div>
    `).join("");
  } catch (e) {
    box.innerHTML = `<div style="color:var(--err);font-size:13px">Erro: ${e.message}</div>`;
  }
}

window.__nickiaDelete = async function(id) {
  const ok = await modalConfirm({
    title: "Excluir narração?",
    body: `Isso vai apagar o áudio #${id.slice(0,6)} (WAV e MP3). Essa ação não pode ser desfeita.`,
    confirmText: "Excluir",
    cancelText: "Cancelar",
    danger: true,
  });
  if (!ok) return;
  try {
    await api.deleteOutput(id);
    refresh();
  } catch (e) {
    modalAlert("Erro ao excluir", e.message);
  }
};

window.__nickiaRename = async function(id) {
  const item = document.querySelector(`.history-item[data-id="${id}"]`);
  const nameEl = item?.querySelector(".fname");
  const atual = nameEl ? nameEl.textContent.trim() : "";

  const nome = await modalPrompt({
    title: "Renomear narração",
    body: "Escolha um nome fácil de identificar depois:",
    placeholder: "ex.: vestido azul, promoção de natal",
    initial: atual,
    confirmText: "Salvar",
    cancelText: "Cancelar",
  });
  if (nome === null) return;
  const limpo = String(nome).trim();
  if (!limpo) {
    modalAlert("Nome vazio", "Digite algum texto para salvar.");
    return;
  }
  try {
    await api.renameOutput(id, limpo);
    refresh();
  } catch (e) {
    modalAlert("Erro ao renomear", e.message);
  }
};

async function onUploadVoice() {
  const name = $("#vname").value.trim();
  const f = $("#vfile").files[0];
  if (!name) { modalAlert("Falta o nome", "Escolha um nome curto para essa voz (ex.: mae)."); return; }
  if (!f) { modalAlert("Falta o arquivo", "Escolha um arquivo de áudio ou vídeo para enviar."); return; }

  $("#vbtn").disabled = true;
  showMsg($("#vmsg"), "Enviando e convertendo...", "ok");
  try {
    const d = await api.uploadVoice(name, f);
    showMsg($("#vmsg"), `Voz "${d.voice.replace(/\.wav$/, "")}" salva (${d.size_kb} KB)`, "ok");
    $("#vfile").value = ""; $("#vname").value = "";
    await loadVoices();
  } catch (e) {
    showMsg($("#vmsg"), "Erro: " + e.message, "err");
  } finally {
    $("#vbtn").disabled = false;
  }
}

export async function loadVoices() {
  try {
    const d = await api.getVoices();
    const sel = $("#voice");
    const prev = sel.value;
    sel.innerHTML = "";
    for (const v of d.voices) {
      const o = document.createElement("option");
      o.value = v; o.textContent = v.replace(/\.wav$/, "");
      sel.appendChild(o);
    }
    if (prev) sel.value = prev;
    const vl = $("#vlist");
    vl.innerHTML = d.voices.length
      ? d.voices.map(v => `<span class="voice-chip"><i class="ri-user-voice-line"></i>${escapeHtml(v.replace(/\.wav$/, ""))}</span>`).join("")
      : '<span style="color:var(--muted);font-size:12px">Nenhuma voz cadastrada ainda.</span>';
  } catch (e) { console.error(e); }
}
