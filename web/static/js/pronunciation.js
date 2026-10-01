// Dicionario de pronuncia editavel.
import * as api from "./api.js";
import { $, showMsg, escapeHtml } from "./ui.js";

export function init() {
  const btn = $("#pronAdd");
  if (!btn) return;
  btn.addEventListener("click", onAdd);
  $("#pronKey").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); $("#pronVal").focus(); }
  });
  $("#pronVal").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); onAdd(); }
  });
  load();
}

async function load() {
  const box = $("#pronRulesList");
  box.innerHTML = '<div style="color:var(--muted);font-size:13px">Carregando...</div>';
  try {
    const d = await fetch("/pronunciation").then(r => r.json());
    const entries = Object.entries(d.rules || {});
    if (!entries.length) {
      box.innerHTML = '<div class="pron-empty">Nenhuma regra ainda.</div>';
      return;
    }
    box.innerHTML = entries.map(([k, v]) => `
      <div class="pron-row" data-key="${escapeHtml(k)}">
        <span class="from">${escapeHtml(k)}</span>
        <span class="sep"><i class="ri-arrow-right-line"></i></span>
        <span class="to">${escapeHtml(v)}</span>
        <button class="danger" onclick="window.__nickiaPronDel('${escapeHtml(k)}')">
          <i class="ri-delete-bin-line"></i>
        </button>
      </div>
    `).join("");
  } catch (e) {
    box.innerHTML = `<div style="color:var(--err);font-size:13px">Erro: ${escapeHtml(e.message)}</div>`;
  }
}

async function save(rules) {
  const r = await fetch("/pronunciation", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rules }),
  });
  if (!r.ok) throw new Error(await r.text());
}

async function onAdd() {
  const key = $("#pronKey").value.trim();
  const val = $("#pronVal").value.trim();
  if (!key || !val) {
    showMsg($("#pronMsg"), "Preencha os dois campos.", "err");
    return;
  }
  try {
    const d = await fetch("/pronunciation").then(r => r.json());
    const rules = Object.entries(d.rules || {}).map(([k, v]) => ({ key: k, value: v }));
    const lower = key.toLowerCase();
    const idx = rules.findIndex(r => r.key.toLowerCase() === lower);
    if (idx >= 0) rules[idx].value = val;
    else rules.push({ key: lower, value: val });
    await save(rules);
    $("#pronKey").value = "";
    $("#pronVal").value = "";
    showMsg($("#pronMsg"), "Regra salva.", "ok");
    load();
  } catch (e) {
    showMsg($("#pronMsg"), "Erro: " + e.message, "err");
  }
}

window.__nickiaPronDel = async function(key) {
  try {
    const d = await fetch("/pronunciation").then(r => r.json());
    const rules = Object.entries(d.rules || {})
      .filter(([k]) => k !== key)
      .map(([k, v]) => ({ key: k, value: v }));
    await save(rules);
    load();
  } catch (e) {
    alert("Erro: " + e.message);
  }
};
