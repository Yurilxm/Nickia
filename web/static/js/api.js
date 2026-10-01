// Chamadas HTTP e polling de jobs.

export async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`HTTP ${r.status}: ${txt.slice(0, 300)}`);
  }
  return r.json();
}

export async function getVoices() {
  return fetchJSON("/voices");
}

export async function getOutputs() {
  return fetchJSON("/outputs");
}

export async function deleteOutput(id) {
  return fetchJSON("/outputs/" + id, { method: "DELETE" });
}

export async function renameOutput(id, name) {
  return fetchJSON("/outputs/" + id, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export async function uploadVoice(name, file) {
  const fd = new FormData();
  fd.append("name", name);
  fd.append("file", file);
  return fetchJSON("/voices/upload", { method: "POST", body: fd });
}

export async function startGenerate(body) {
  return fetchJSON("/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function startVideoCompose(fd) {
  return fetchJSON("/video/compose", { method: "POST", body: fd });
}

export async function cancelJob(jid) {
  return fetchJSON(`/jobs/${jid}/cancel`, { method: "POST" });
}

export async function getJob(jid) {
  return fetchJSON("/jobs/" + jid);
}

// Polling generico. onTick(job) -> retorna true para parar.
export function pollJob(jid, onTick, intervalMs = 1000) {
  return new Promise((resolve) => {
    const iv = setInterval(async () => {
      try {
        const j = await getJob(jid);
        const stop = onTick(j);
        if (stop || j.status === "done" || j.status === "error" || j.status === "cancelled") {
          clearInterval(iv);
          resolve(j);
        }
      } catch (e) {
        console.error("poll erro:", e);
      }
    }, intervalMs);
  });
}
