// Ponto de entrada: navegacao entre abas + init dos modulos.
import * as audio from "./audio.js";
import * as video from "./video.js";
import * as history from "./history.js";
import * as pronunciation from "./pronunciation.js";

function initTabs() {
  const tabs = document.querySelectorAll(".tab");
  const panels = document.querySelectorAll(".tab-panel");
  tabs.forEach(t => {
    t.addEventListener("click", () => {
      const target = t.dataset.tab;
      tabs.forEach(x => x.classList.toggle("active", x === t));
      panels.forEach(p => p.classList.toggle("active", p.id === "panel-" + target));
    });
  });
}

function safe(name, fn) {
  try { fn(); console.log("[main] " + name + " OK"); }
  catch (e) { console.error("[main] " + name + " FALHOU:", e); }
}

document.addEventListener("DOMContentLoaded", () => {
  safe("tabs", initTabs);
  safe("audio", audio.init);
  safe("video", video.init);
  safe("history", history.init);
  safe("pronunciation", pronunciation.init);
  safe("loadVoices", history.loadVoices);
});
