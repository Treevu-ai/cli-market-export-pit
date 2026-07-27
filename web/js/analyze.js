import {
  RECOMMENDATION_LABELS,
  fetchAgentsStatus,
  fetchReport,
  generateFicha,
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
const fichaBtn = document.getElementById("ficha-btn");
const fichaOptions = document.getElementById("ficha-options");
const fichaPanel = document.getElementById("ficha-panel");
const fichaMarkdown = document.getElementById("ficha-markdown");
const fichaDownload = document.getElementById("ficha-download");
const fichaSegment = document.getElementById("ficha-segment");
const fichaStage = document.getElementById("ficha-stage");

let currentRunId = null;
let currentFichaMarkdown = "";
let fichaAvailable = false;

const RECENT_RUNS_KEY = "pit_recent_runs";
const RECENT_RUNS_MAX = 8;
const GAUGE_CIRCUMFERENCE = 263.9;

function loadRecentRuns() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_RUNS_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveRecentRun(entry) {
  const runs = loadRecentRuns().filter((run) => run.id !== entry.id);
  runs.unshift(entry);
  localStorage.setItem(RECENT_RUNS_KEY, JSON.stringify(runs.slice(0, RECENT_RUNS_MAX)));
  renderRecentRuns();
}

function renderRecentRuns() {
  const list = document.getElementById("recent-runs-list");
  const emptyMsg = document.getElementById("recent-runs-empty");
  if (!list) return;
  const runs = loadRecentRuns();
  list.innerHTML = "";
  if (emptyMsg) emptyMsg.classList.toggle("hidden", runs.length > 0);
  runs.forEach((run) => {
    const item = document.createElement("div");
    item.className = "recent-run-item";
    item.innerHTML = `
      <span class="recent-run-name">${run.query} · ${run.target_market}</span>
      <span class="recent-run-score">${run.score ?? "—"}</span>
    `;
    item.addEventListener("click", () => loadRun(run.id));
    list.appendChild(item);
  });
}

async function loadRun(runId) {
  clearError();
  setStatus("running", "Cargando run…");
  try {
    const report = await fetchReport(runId);
    renderReport(report);
    setStatus("done", "Completado");
  } catch (error) {
    setStatus("error", "Error");
    showError(error.message || String(error));
  }
}

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

async function refreshAgentsStatus() {
  if (!fichaBtn) return;
  try {
    const status = await fetchAgentsStatus();
    fichaAvailable = Boolean(status.ficha_available);
    fichaBtn.disabled = !fichaAvailable || !currentRunId;
    fichaBtn.title = fichaAvailable
      ? "Genera una ficha ejecutiva con agentes de inteligencia de producto"
      : status.reason || "Agentes no disponibles en el servidor";
  } catch {
    fichaAvailable = false;
    fichaBtn.disabled = true;
    fichaBtn.title = "No se pudo comprobar el estado de los agentes";
  }
}

refreshAgentsStatus();

function resetFichaPanel() {
  currentFichaMarkdown = "";
  if (fichaPanel) fichaPanel.classList.add("hidden");
  if (fichaMarkdown) fichaMarkdown.textContent = "";
}

function showFichaPanel(markdown) {
  currentFichaMarkdown = markdown;
  if (fichaMarkdown) fichaMarkdown.textContent = markdown;
  fichaPanel?.classList.remove("hidden");
  fichaPanel?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

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

function renderChecklist(checklist = []) {
  const box = document.getElementById("checklist-box");
  if (!box) return;
  if (!checklist.length) {
    box.classList.add("hidden");
    box.innerHTML = "";
    return;
  }
  box.classList.remove("hidden");
  box.innerHTML = `
    <h4>Como mejorar este analisis</h4>
    <ul>
      ${checklist
        .map(
          (item) => `
        <li class="checklist-priority-${item.priority}">
          <strong>${item.priority}</strong> — ${item.title}: ${item.action}
        </li>`,
        )
        .join("")}
    </ul>
  `;
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

  const gauge = document.getElementById("gauge-progress");
  if (gauge) {
    const pct = Math.max(0, Math.min(100, Number(score.opportunity_score) || 0));
    const offset = GAUGE_CIRCUMFERENCE - (pct / 100) * GAUGE_CIRCUMFERENCE;
    requestAnimationFrame(() => {
      gauge.style.strokeDashoffset = String(offset);
    });
  }
  document.getElementById("score-version").textContent = score.score_version ?? "—";
  document.getElementById("run-id").textContent = report.run_id;

  const recPill = document.getElementById("recommendation-pill");
  recPill.textContent = rec.label;
  recPill.className = `status-pill ${rec.className}`;

  const pdfLink = document.getElementById("pdf-link");
  if (pdfLink) pdfLink.href = reportPdfUrl(report.run_id);
  const reportLink = document.getElementById("report-link");
  if (reportLink) reportLink.href = `/report.html?run_id=${encodeURIComponent(report.run_id)}`;

  currentRunId = report.run_id;
  resetFichaPanel();
  fichaOptions?.classList.remove("hidden");
  if (fichaBtn) {
    fichaBtn.disabled = !fichaAvailable;
    fichaBtn.textContent = "Generar Ficha";
  }

  renderDimensions(score.dimensions || {});
  renderComplementary(report.evidence_summary || {});
  renderChecklist(report.improvement_checklist || []);
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
renderRecentRuns();

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

if (fichaBtn) {
  fichaBtn.addEventListener("click", async () => {
    if (!currentRunId || !fichaAvailable) return;
    clearError();
    fichaBtn.disabled = true;
    fichaBtn.textContent = "Generando ficha…";
    setStatus("running", "Agentes en ejecución…");

    try {
      const result = await generateFicha(currentRunId, {
        segment: fichaSegment?.value?.trim() || "exportadores y retail premium",
        stage: fichaStage?.value || "concepto",
      });
      showFichaPanel(result.dossier_markdown || "");
      setStatus("done", "Ficha generada");
    } catch (error) {
      setStatus("error", "Error");
      showError(error.message || String(error));
    } finally {
      fichaBtn.disabled = !fichaAvailable;
      fichaBtn.textContent = "Generar Ficha";
    }
  });
}

if (fichaDownload) {
  fichaDownload.addEventListener("click", () => {
    if (!currentFichaMarkdown || !currentRunId) return;
    const blob = new Blob([currentFichaMarkdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `ficha-${currentRunId}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
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
      saveRecentRun({
        id: report.run_id,
        query: report.query,
        target_market: report.target_market,
        score: report.score?.opportunity_score,
      });
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
