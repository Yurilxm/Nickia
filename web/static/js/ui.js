// Utilitarios de UI.

export const STAGE_LABEL = {
  queued: "Na fila...",
  loading: "Carregando o motor de voz...",
  preparing: "Analisando...",
  generating: "Gerando...",
  concatenating: "Juntando as partes...",
  converting: "Convertendo...",
  done: "Pronto!",
  error: "Erro",
  cancelled: "Cancelado",
};

// Aceita tanto "#id" quanto "id" — internamente usa getElementById
export function $(selector) {
  if (typeof selector !== "string") return selector;
  const id = selector.startsWith("#") ? selector.slice(1) : selector;
  return document.getElementById(id);
}

export function showMsg(el, text, kind) {
  const icon = kind === "ok" ? "check-line" : (kind === "warn" ? "alert-line" : "error-warning-line");
  el.innerHTML = `<i class="ri-${icon}"></i> ${escapeHtml(text)}`;
  el.className = "status-msg on " + kind;
  el.style.display = "flex";
}
export function hideMsg(el) { el.className = "status-msg"; el.style.display = "none"; }

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

// group = "Audio" ou "Video"
export function setProgress(group, pct, stage, sent) {
  const fill = $(`pfill${group}`);
  const pctEl = $(`ppct${group}`);
  const stageEl = $(`pstage${group}`);
  const sentEl = $(`psent${group}`);
  if (fill) fill.style.width = Math.max(0, Math.min(100, pct)) + "%";
  if (pctEl) pctEl.textContent = Math.round(pct) + "%";
  if (stageEl) stageEl.textContent = stage || "";
  if (sentEl && sent !== undefined) sentEl.textContent = sent || "";
}
