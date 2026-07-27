import {
  RECOMMENDATION_LABELS,
  fetchAgentsStatus,
  fetchReport,
  generateFicha,
  reportPdfUrl,
} from "./pit-api.js";

const emptyState = document.getElementById("empty-state");
const errorState = document.getElementById("error-state");
const reportContent = document.getElementById("report-content");
const jsonToggle = document.getElementById("json-toggle");
const jsonRaw = document.getElementById("json-raw");
const fichaBtn = document.getElementById("ficha-btn");
const fichaOptions = document.getElementById("ficha-options");
const fichaPanel = document.getElementById("ficha-panel");
const fichaMarkdown = document.getElementById("ficha-markdown");
const fichaDownload = document.getElementById("ficha-download");
const fichaSegment = document.getElementById("ficha-segment");
const fichaStage = document.getElementById("ficha-stage");

const DOMAIN_LABELS = {
  science: "Ciencia",
  patent: "Patentes",
  trend: "Tendencias",
  trade: "Comercio exterior",
  commerce: "Retail / góndola",
  regulatory: "Regulatorio",
  sustainability: "Sostenibilidad",
  technology_scout: "I+D y proyectos",
};

const COMPLEMENTARY_KEYS = {
  comtrade_aggregation: {
    title: "Comercio exterior",
    detail: (data) =>
      `${data.trade_records_count ?? 0} registros · tendencia ${data.trend ?? "—"} (Comtrade)`,
  },
  climatiq_aggregation: {
    title: "Sostenibilidad",
    detail: (data) =>
      data?.activity_count != null
        ? `${data.activity_count} actividades de huella (Climatiq)`
        : "Sin datos de carbono",
  },
  techscout_aggregation: {
    title: "I+D y proyectos",
    detail: (data) =>
      data?.total_projects != null
        ? `${data.total_projects} proyectos (CORDIS, NIH, NSF)`
        : "Sin proyectos de I+D",
  },
};

let currentRunId = null;
let currentFichaMarkdown = "";
let fichaAvailable = false;

function showError(message) {
  errorState.textContent = message;
  errorState.classList.remove("hidden");
}

function renderDomainBento(dimensions = {}) {
  const grid = document.getElementById("domain-bento");
  grid.innerHTML = "";
  const entries = Object.entries(dimensions);
  if (!entries.length) {
    grid.innerHTML = '<p style="color:var(--text-secondary);">Sin dominios puntuados en este run.</p>';
    return;
  }
  entries.forEach(([domain, data]) => {
    const row = document.createElement("div");
    row.className = "dimension-row";
    const pct = Math.max(0, Math.min(100, Number(data.score) || 0));
    row.innerHTML = `
      <span>${DOMAIN_LABELS[domain] || domain}</span>
      <div class="dimension-bar"><span style="width:${pct}%"></span></div>
      <span>${data.score ?? "—"}</span>
    `;
    grid.appendChild(row);
  });
}

function renderRegulatoryHub(summaries) {
  const box = document.getElementById("regulatory-hub");
  const reg = summaries.regulatory_aggregation;
  if (!reg || !reg.total_records) {
    return;
  }
  box.innerHTML = `
    <p style="margin:0 0 0.75rem;font-size:0.9rem;color:var(--on-surface-variant);">
      <strong>${reg.total_records}</strong> registros regulatorios encontrados.
    </p>
    ${(reg.sources || [])
      .map(
        (s) => `<div class="reg-source-row"><span>${s.source}</span><span class="data-hash">${s.record_count}</span></div>`,
      )
      .join("")}
  `;
}

function renderCommerceBenchmarks(summaries) {
  const box = document.getElementById("commerce-benchmarks");
  const commerce = summaries.climarket_aggregation;
  if (!commerce || commerce.price_max == null) {
    return;
  }
  const max = commerce.price_max || 1;
  const rows = [
    { label: "Precio mínimo", value: commerce.price_min },
    { label: "Precio promedio", value: commerce.price_avg },
    { label: "Precio máximo", value: commerce.price_max },
  ];
  box.innerHTML = `
    ${rows
      .map(
        (r) => `
      <div class="price-bar-row">
        <div class="price-bar-label"><span>${r.label}</span><span>${r.value != null ? `S/ ${r.value}` : "—"}</span></div>
        <div class="price-bar-track"><span style="width:${r.value != null ? Math.min(100, (r.value / max) * 100) : 0}%"></span></div>
      </div>`,
      )
      .join("")}
    <p style="margin:0.5rem 0 0;font-size:0.8rem;color:var(--on-surface-variant);">
      ${commerce.stores_compared ?? 0} tiendas comparadas · ${commerce.shelf_products_count ?? 0} productos de góndola (CLI Market).
    </p>
  `;
}

function renderComplementary(summaries) {
  const grid = document.getElementById("complementary-grid");
  grid.innerHTML = "";
  const entries = Object.entries(COMPLEMENTARY_KEYS)
    .map(([key, meta]) => [key, meta, summaries[key]])
    .filter(([, , data]) => data != null);
  if (!entries.length) {
    grid.innerHTML =
      '<p style="color:var(--text-secondary);font-size:0.85rem;margin:0;">Sin agregaciones complementarias en este run.</p>';
    return;
  }
  entries.forEach(([, meta, data]) => {
    const card = document.createElement("div");
    card.className = "complementary-card";
    card.innerHTML = `<strong>${meta.title}</strong><p>${meta.detail(data)}</p>`;
    grid.appendChild(card);
  });
}

function renderChecklist(checklist = []) {
  const box = document.getElementById("checklist-box");
  if (!checklist.length) {
    box.classList.add("hidden");
    return;
  }
  box.classList.remove("hidden");
  box.innerHTML = `
    <h4>Cómo mejorar este análisis</h4>
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

function renderSources(sources = []) {
  const list = document.getElementById("sources-list");
  list.innerHTML = "";
  if (!sources.length) {
    list.innerHTML = '<p style="color:var(--text-secondary);font-size:0.85rem;">Sin fuentes registradas.</p>';
    return;
  }
  sources.forEach((s) => {
    const item = document.createElement("div");
    item.className = "source-item";
    const shortHash = s.checksum ? `${s.checksum.slice(0, 8)}…${s.checksum.slice(-6)}` : "—";
    item.innerHTML = `
      <span class="source-name">${s.source}</span>
      <span class="data-hash"><span class="material-symbols-outlined" style="font-size:12px;">lock</span>${shortHash}</span>
      <span class="pill-status ${s.status === "success" ? "pill-status-go" : "pill-status-flag"}">${s.status}</span>
    `;
    list.appendChild(item);
  });
}

function resetFichaPanel() {
  currentFichaMarkdown = "";
  fichaPanel.classList.add("hidden");
  fichaMarkdown.textContent = "";
}

function showFichaPanel(markdown) {
  currentFichaMarkdown = markdown;
  fichaMarkdown.textContent = markdown;
  fichaPanel.classList.remove("hidden");
}

function renderReport(report) {
  const score = report.score || {};
  const rec = RECOMMENDATION_LABELS[score.recommendation] || {
    label: score.recommendation || "—",
    className: "status-idle",
  };

  document.getElementById("verdict-run-id").textContent = report.run_id;
  document.getElementById("verdict-cutoff").textContent = report.cutoff_at
    ? new Date(report.cutoff_at).toLocaleString("es-PE")
    : "—";
  document.getElementById("verdict-title").textContent = `${report.query || "Consulta"} → ${report.target_market || "—"}`;
  document.getElementById("verdict-subtitle").textContent = report.application || "";

  const recPill = document.getElementById("verdict-recommendation");
  recPill.textContent = rec.label;
  recPill.className = `pill-status ${rec.className === "status-done" ? "pill-status-go" : rec.className === "status-running" ? "pill-status-conditional" : rec.className === "status-error" ? "pill-status-insufficient" : "pill-status-flag"}`;

  document.getElementById("verdict-score-value").textContent = score.opportunity_score ?? "—";
  document.getElementById("verdict-coverage").textContent = score.coverage_factor ?? "—";
  document.getElementById("verdict-version").textContent = score.score_version ?? "—";

  renderDomainBento(score.dimensions || {});
  renderRegulatoryHub(report.evidence_summary || {});
  renderCommerceBenchmarks(report.evidence_summary || {});
  renderComplementary(report.evidence_summary || {});
  renderChecklist(report.improvement_checklist || []);
  renderSources(report.sources || []);

  document.getElementById("pdf-link").href = reportPdfUrl(report.run_id);
  jsonRaw.textContent = JSON.stringify(report, null, 2);

  currentRunId = report.run_id;
  resetFichaPanel();
  fichaOptions.classList.remove("hidden");
  fichaBtn.disabled = !fichaAvailable;

  emptyState.classList.add("hidden");
  reportContent.classList.remove("hidden");
}

async function refreshAgentsStatus() {
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
  }
}

jsonToggle.addEventListener("click", () => jsonRaw.classList.toggle("hidden"));

fichaBtn.addEventListener("click", async () => {
  if (!currentRunId || !fichaAvailable) return;
  errorState.classList.add("hidden");
  fichaBtn.disabled = true;
  try {
    const result = await generateFicha(currentRunId, {
      segment: fichaSegment.value.trim() || "exportadores y retail premium",
      stage: fichaStage.value || "concepto",
    });
    showFichaPanel(result.dossier_markdown || "");
  } catch (error) {
    showError(error.message || String(error));
  } finally {
    fichaBtn.disabled = !fichaAvailable;
  }
});

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

async function init() {
  const params = new URLSearchParams(window.location.search);
  const runId = params.get("run_id");
  if (!runId) return;

  await refreshAgentsStatus();
  try {
    const report = await fetchReport(runId);
    renderReport(report);
  } catch (error) {
    emptyState.classList.add("hidden");
    showError(error.message || String(error));
  }
}

init();
