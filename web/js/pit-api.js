/** PIT API client for the web frontend */
export function getApiBase() {
  if (window.PIT_API_BASE) return window.PIT_API_BASE.replace(/\/$/, "");
  if (window.location.protocol === "file:") return "http://127.0.0.1:8000";
  return window.location.origin.replace(/\/$/, "");
}

export async function pitRequest(path, options = {}) {
  const headers = {
    Accept: "application/json",
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {}),
  };
  if (window.PIT_API_KEY) {
    headers["X-API-Key"] = window.PIT_API_KEY;
  }
  const response = await fetch(`${getApiBase()}${path}`, {
    ...options,
    headers,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || payload.message || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}

export async function runFullPipeline(body) {
  const envelope = await pitRequest("/v1/research-runs/full", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return envelope.data;
}

export async function fetchReport(runId) {
  const envelope = await pitRequest(`/v1/research-runs/${runId}/report`);
  return envelope.data;
}

export function reportPdfUrl(runId) {
  return `${getApiBase()}/v1/research-runs/${runId}/report.pdf`;
}

export const RECOMMENDATION_LABELS = {
  Investigate: { label: "Investigar", className: "status-done" },
  Validate: { label: "Validar", className: "status-running" },
  Deprioritize: { label: "Depriorizar", className: "status-idle" },
  "Insufficient evidence": { label: "Evidencia insuficiente", className: "status-error" },
};
