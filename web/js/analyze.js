import {
  RECOMMENDATION_LABELS,
  fetchReport,
  getApiBase,
  reportPdfUrl,
  runFullPipeline,
} from "./pit-api.js";

const form = document.getElementById("analyze-form");
const statusPill = document.getElementById("status-pill");
const emptyState = document.getElementById("empty-state");
const resultsContent = document.getElementById("results-content");
const errorState = document.getElementById("error-state");
const submitBtn = document.getElementById("submit-btn");
const apiBaseEl = document.getElementById("api-base");
const jsonToggle = document.getElementById("json-toggle");
const jsonRaw = document.getElementById("json-raw");

const COMPLEMENTARY_KEYS = {
  regulatory_aggregation: {
    title: "Regulación",
    detail: (data) => {
      const total = data?.total_records;
      return total != null ? `${total} registros (OpenFDA, EUR-Lex, FoodData)` : "Sin datos regulatorios";
    },
  },
  climatiq_aggregation: {
    title: "Sostenibilidad",
    detail: (data) => {
      const count = data?.activity_count;
      return count != null ? `${count} actividades de huella (Climatiq)` : "Sin datos de carbono";
    },
  },
  techscout_aggregation: {
    title: "I+D y proyectos",
    detail: (data) => {
      const total = data?.total_projects;
      return total != null ? `${total} proyectos (CORDIS, NIH, NSF)` : "Sin proyectos de I+D";
    },
  },
};

if (apiBaseEl) apiBaseEl.textContent = getApiBase();

function setStatus(kind, label) {
  if (!statusPill) return;
  statusPill.className = `status-pill status-${kind}`;
  statusPill.textContent = label;
}

function showError(message) {
  if (errorState) {
    errorState.textContent = message;
    errorState.classList.remove("hidden");
  }
}

function clearError() {
  if (errorState) {
    errorState.textContent = "";
    errorState.classList.add("hidden");
  }
}

function renderDimensions(dimensions = {}) {
  const list = document.getElementById("dimension-list");
  if (!list) return;
  list.innerHTML = "";
  Object.entries(dimensions).forEach(([domain, data]) => {
    const row = document.createElement("div");
    row.className = "dimension-row";
    row.innerHTML = `
      <span>${domain}</span>
      <div class="dimension-bar"><span style="width:${Math.min(100, data.score || 0)}%"></span></div>
      <span>${data.score ?? "—"}</span>
    `;
    list.appendChild(row);
  });
}

function renderComplementary(evidenceSummary = {}) {
  const grid = document.getElementById("complementary-grid");
  if (!grid) return;
  grid.innerHTML = "";

  const entries = Object.entries(COMPLEMENTARY_KEYS)
    .map(([key, meta]) => [key, meta, evidenceSummary[key]])
    .filter(([, , data]) => data != null);

  if (!entries.length) {
    grid.innerHTML =
      '<p style="color:var(--text-secondary);font-size:0.85rem;margin:0;">No hay agregaciones complementarias en este run (conectores opcionales pueden no haber corrido).</p>';
    return;
  }

  entries.forEach(([key, meta, data]) => {
    const card = document.createElement("div");
    card.className = "complementary-card";
    card.innerHTML = `<strong>${meta.title}</strong><p>${meta.detail(data)}</p>`;
    grid.appendChild(card);
  });
}

function renderEvidence(evidenceSummary = {}) {
  const grid = document.getElementById("evidence-grid");
  if (!grid) return;
  grid.innerHTML = "";
  const entries = Object.entries(evidenceSummary).filter(([key]) => key !== "pipeline_warnings");
  if (!entries.length) {
    grid.innerHTML = '<p class="empty-state" style="padding:1rem;">Sin agregaciones de evidencia.</p>';
    return;
  }
  entries.forEach(([key, value]) => {
    const details = document.createElement("details");
    details.className = "evidence-item";
    details.open = entries.length <= 3;
    details.innerHTML = `
      <summary>${key}</summary>
      <div class="evidence-body">${JSON.stringify(value, null, 2)}</div>
    `;
    grid.appendChild(details);
  });
}

function renderReport(report) {
  const score = report.score || {};
  const rec = RECOMMENDATION_LABELS[score.recommendation] || {
    label: score.recommendation || "—",
    className: "status-idle",
  };

  document.getElementById("run-title").textContent = report.query || "Consulta";
  document.getElementById("run-meta").textContent = `${report.target_market || "—"} · ${report.application || ""}`;
  document.getElementById("score-value").textContent = score.opportunity_score ?? "—";
  document.getElementById("coverage-value").textContent = score.coverage_factor ?? "—";
  document.getElementById("score-version").textContent = score.score_version ?? "—";
  document.getElementById("run-id").textContent = report.run_id;

  const recPill = document.getElementById("recommendation-pill");
  recPill.textContent = rec.label;
  recPill.className = `status-pill ${rec.className}`;

  const pdfLink = document.getElementById("pdf-link");
  if (pdfLink) pdfLink.href = reportPdfUrl(report.run_id);

  renderDimensions(score.dimensions || {});
  renderComplementary(report.evidence_summary || {});
  renderEvidence(report.evidence_summary || {});

  const alerts = [
    ...(score.alerts || []),
    ...((report.evidence_summary?.pipeline_warnings?.failures) || []),
  ];
  const alertsBox = document.getElementById("alerts-box");
  if (alertsBox) {
    if (alerts.length) {
      alertsBox.innerHTML = `<strong>Advertencias del pipeline</strong><ul>${alerts.map((item) => `<li>${item}</li>`).join("")}</ul>`;
      alertsBox.classList.remove("hidden");
    } else {
      alertsBox.classList.add("hidden");
    }
  }

  if (jsonRaw) jsonRaw.textContent = JSON.stringify(report, null, 2);

  emptyState?.classList.add("hidden");
  resultsContent?.classList.remove("hidden");
}

function prefillFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const query = params.get("query");
  const market = params.get("market");
  if (query) document.getElementById("query").value = query;
  if (market) document.getElementById("target_market").value = market.toUpperCase();
}

prefillFromQuery();

document.querySelectorAll(".preset-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const queryInput = document.getElementById("query");
    const marketSelect = document.getElementById("target_market");
    if (queryInput && button.dataset.query) queryInput.value = button.dataset.query;
    if (marketSelect && button.dataset.market) marketSelect.value = button.dataset.market;
  });
});

if (jsonToggle && jsonRaw) {
  jsonToggle.addEventListener("click", () => {
    jsonRaw.classList.toggle("hidden");
  });
}

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    setStatus("running", "Ejecutando pipeline…");
    submitBtn.disabled = true;

    const body = {
      query: form.query.value.trim(),
      target_market: form.target_market.value,
      application: form.application.value.trim(),
      limit: Number(form.limit.value || 10),
    };
    if (form.hs_code.value.trim()) {
      body.hs_code = form.hs_code.value.trim();
    }

    try {
      const run = await runFullPipeline(body);
      setStatus("running", "Generando reporte…");
      const report = await fetchReport(run.id);
      renderReport(report);
      setStatus("done", "Completado");
    } catch (error) {
      setStatus("error", "Error");
      showError(error.message || String(error));
      emptyState?.classList.remove("hidden");
      resultsContent?.classList.add("hidden");
    } finally {
      submitBtn.disabled = false;
    }
  });
}
