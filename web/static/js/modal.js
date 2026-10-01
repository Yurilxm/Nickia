// Modal customizado (substitui alert/confirm/prompt do navegador).

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

// showModal({ kind, title, body, placeholder, initial, confirmText, cancelText, danger })
// kind: "alert" | "confirm" | "prompt"
// retorna: alert -> true; confirm -> true/false; prompt -> string/null
export function showModal(opts = {}) {
  return new Promise((resolve) => {
    const kind = opts.kind || "alert";
    const title = opts.title || "";
    const body = opts.body || "";
    const confirmText = opts.confirmText || (kind === "prompt" ? "Salvar" : "OK");
    const cancelText = opts.cancelText !== undefined
      ? opts.cancelText
      : (kind === "alert" ? null : "Cancelar");
    const danger = !!opts.danger;
    const placeholder = opts.placeholder || "";
    const initial = opts.initial || "";

    const iconName = kind === "prompt" ? "edit"
      : danger ? "error-warning"
      : kind === "confirm" ? "question"
      : "information";

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-head">
          <i class="ri-${iconName}-line"></i>
          <h3>${escapeHtml(title)}</h3>
        </div>
        ${body ? `<div class="modal-body">${escapeHtml(body)}</div>` : ""}
        ${kind === "prompt" ? `<input type="text" class="modal-input" placeholder="${escapeHtml(placeholder)}" value="${escapeHtml(initial)}">` : ""}
        <div class="modal-actions">
          ${cancelText ? `<button class="ghost modal-cancel">${escapeHtml(cancelText)}</button>` : ""}
          <button class="modal-confirm ${danger ? "danger-solid" : ""}">${escapeHtml(confirmText)}</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const input = overlay.querySelector(".modal-input");
    const btnConfirm = overlay.querySelector(".modal-confirm");
    const btnCancel = overlay.querySelector(".modal-cancel");
    const prevFocus = document.activeElement;

    function close(result) {
      document.removeEventListener("keydown", onKey, true);
      overlay.classList.remove("modal-open");
      overlay.classList.add("modal-closing");
      setTimeout(() => {
        overlay.remove();
        try { if (prevFocus && prevFocus.focus) prevFocus.focus(); } catch (_) {}
        resolve(result);
      }, 130);
    }

    function onConfirm() {
      if (kind === "prompt") close(input.value);
      else close(true);
    }
    function onCancel() {
      if (kind === "prompt") close(null);
      else close(false);
    }
    function onKey(e) {
      if (e.key === "Escape") { e.preventDefault(); onCancel(); }
      else if (e.key === "Enter") {
        e.preventDefault();
        onConfirm();
      }
    }

    btnConfirm.addEventListener("click", onConfirm);
    if (btnCancel) btnCancel.addEventListener("click", onCancel);

    overlay.addEventListener("mousedown", (e) => {
      if (e.target === overlay) onCancel();
    });

    document.addEventListener("keydown", onKey, true);

    requestAnimationFrame(() => {
      overlay.classList.add("modal-open");
      if (input) { input.focus(); input.select(); }
      else btnConfirm.focus();
    });
  });
}

// Atalhos
export const modalAlert = (title, body) => showModal({ kind: "alert", title, body });
export const modalConfirm = (opts) => showModal({ kind: "confirm", ...opts });
export const modalPrompt = (opts) => showModal({ kind: "prompt", ...opts });
