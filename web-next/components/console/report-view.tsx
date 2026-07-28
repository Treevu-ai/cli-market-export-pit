"use client";

import { useState } from "react";
import {
  RECOMMENDATION_LABELS,
  reportPdfUrl,
  type ReportData,
} from "@/lib/pit-api";
import { ScoreGauge } from "./score-gauge";
import { DomainGrid } from "./domain-grid";

const TONE_CLASSES: Record<string, string> = {
  go: "bg-[#64ffda]/15 text-[#64ffda]",
  conditional: "bg-[#ffd700]/15 text-[#ffd700]",
  flag: "bg-[#e11d48]/15 text-[#e11d48]",
  insufficient: "bg-foreground/10 text-muted-foreground",
};

const PRIORITY_CLASSES: Record<string, string> = {
  high: "text-[#e11d48]",
  medium: "text-[#ffd700]",
  low: "text-muted-foreground",
};

const COMPLEMENTARY_KEYS: Record<string, { title: string; detail: (data: any) => string }> = {
  comtrade_aggregation: {
    title: "Comercio exterior",
    detail: (data) => `${data.trade_records_count ?? 0} registros · tendencia ${data.trend ?? "—"} (Comtrade)`,
  },
  climatiq_aggregation: {
    title: "Sostenibilidad",
    detail: (data) =>
      data?.activity_count != null ? `${data.activity_count} actividades de huella (Climatiq)` : "Sin datos de carbono",
  },
  techscout_aggregation: {
    title: "I+D y proyectos",
    detail: (data) =>
      data?.total_projects != null ? `${data.total_projects} proyectos (CORDIS, NIH, NSF)` : "Sin proyectos de I+D",
  },
  bcrp_aggregation: {
    title: "Contexto macro (BCRP)",
    detail: (data) => {
      const series = data?.series?.[0];
      if (!series) return "Sin datos macro del BCRP";
      return `${series.name}: ${series.latest_value} (${series.latest_period})`;
    },
  },
};

type Props = {
  report: ReportData;
  fichaAvailable: boolean;
  onGenerateFicha: (segment: string, stage: string) => Promise<string | null>;
};

export function ReportView({ report, fichaAvailable, onGenerateFicha }: Props) {
  const [showJson, setShowJson] = useState(false);
  const [fichaMarkdown, setFichaMarkdown] = useState("");
  const [fichaSegment, setFichaSegment] = useState("exportadores y retail premium");
  const [fichaStage, setFichaStage] = useState("concepto");
  const [fichaGenerating, setFichaGenerating] = useState(false);
  const [fichaError, setFichaError] = useState<string | null>(null);

  const score = report.score;
  const rec = RECOMMENDATION_LABELS[score.recommendation] || { label: score.recommendation || "—", tone: "insufficient" };
  const summaries = report.evidence_summary || {};
  const regulatory = summaries.regulatory_aggregation;
  const commerce = summaries.climarket_aggregation;

  const complementary = Object.entries(COMPLEMENTARY_KEYS)
    .map(([key, meta]) => [key, meta, summaries[key]] as const)
    .filter(([, , data]) => data != null);

  async function handleGenerateFicha() {
    setFichaGenerating(true);
    setFichaError(null);
    try {
      const markdown = await onGenerateFicha(fichaSegment, fichaStage);
      if (markdown) setFichaMarkdown(markdown);
    } catch (error) {
      setFichaError(error instanceof Error ? error.message : String(error));
    } finally {
      setFichaGenerating(false);
    }
  }

  function handleDownloadFicha() {
    if (!fichaMarkdown) return;
    const blob = new Blob([fichaMarkdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `ficha-${report.run_id}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-10">
      {/* Verdict header */}
      <section className="flex flex-col gap-6 border border-foreground/10 bg-foreground/[0.02] p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-1 font-mono text-xs text-[#64ffda]">
              🔒 {report.run_id}
            </span>
            <span className="text-xs text-muted-foreground">
              {report.cutoff_at ? new Date(report.cutoff_at).toLocaleString("es-PE") : "—"}
            </span>
          </div>
          <h1 className="mt-2 font-display text-2xl sm:text-3xl">
            {report.query || "Consulta"} → {report.target_market || "—"}
          </h1>
          <p className="mt-1 text-muted-foreground">{report.application}</p>
        </div>
        <div className="flex items-center gap-5">
          <ScoreGauge score={score.opportunity_score} />
          <div>
            <span className={`inline-block rounded-full px-3 py-1 font-mono text-xs ${TONE_CLASSES[rec.tone]}`}>
              {rec.label}
            </span>
            <p className="mt-2 text-xs text-muted-foreground">
              Cobertura: <strong className="text-foreground">{score.coverage_factor ?? "—"}</strong> ·{" "}
              {score.score_version}
            </p>
          </div>
        </div>
      </section>

      {/* Domain grid */}
      <section>
        <h2 className="mb-4 font-display text-xl">Dominios evaluados</h2>
        <DomainGrid dimensions={score.dimensions || {}} />
      </section>

      {/* Regulatory + commerce */}
      <section className="grid gap-4 md:grid-cols-2">
        <div className="border border-foreground/10 p-6">
          <h3 className="mb-4 font-display text-lg">Regulatory Hub</h3>
          {regulatory && regulatory.total_records ? (
            <>
              <p className="mb-3 text-sm text-muted-foreground">
                <strong className="text-foreground">{regulatory.total_records}</strong> registros regulatorios encontrados.
              </p>
              {(regulatory.sources || []).map((s: any) => (
                <div key={s.source} className="flex justify-between border-b border-foreground/10 py-2 text-sm last:border-b-0">
                  <span>{s.source}</span>
                  <span className="font-mono text-[#64ffda]">{s.record_count}</span>
                </div>
              ))}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Sin datos regulatorios en este run.</p>
          )}
        </div>
        <div className="border border-foreground/10 p-6">
          <h3 className="mb-4 font-display text-lg">Commerce: benchmarks de precio</h3>
          {commerce && commerce.price_max != null ? (
            <>
              {[
                { label: "Precio mínimo", value: commerce.price_min },
                { label: "Precio promedio", value: commerce.price_avg },
                { label: "Precio máximo", value: commerce.price_max },
              ].map((row) => (
                <div key={row.label} className="mb-3 last:mb-0">
                  <div className="mb-1 flex justify-between text-xs font-semibold">
                    <span>{row.label}</span>
                    <span>{row.value != null ? `S/ ${row.value}` : "—"}</span>
                  </div>
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-foreground/10">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-[#006b58] to-[#64ffda]"
                      style={{ width: `${row.value != null ? Math.min(100, (row.value / commerce.price_max) * 100) : 0}%` }}
                    />
                  </div>
                </div>
              ))}
              <p className="mt-3 text-xs text-muted-foreground">
                {commerce.stores_compared ?? 0} tiendas comparadas · {commerce.shelf_products_count ?? 0} productos de góndola (CLI Market).
              </p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Sin datos de CLI Market en este run.</p>
          )}
        </div>
      </section>

      {/* Complementary */}
      <section>
        <h2 className="mb-4 font-display text-xl">Evidencia complementaria</h2>
        {complementary.length ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {complementary.map(([key, meta, data]) => (
              <div key={key} className="border border-foreground/10 bg-foreground/[0.02] p-4">
                <strong className="mb-1 block font-display text-sm">{meta.title}</strong>
                <p className="text-sm text-muted-foreground">{meta.detail(data)}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Sin agregaciones complementarias en este run.</p>
        )}
      </section>

      {/* Checklist */}
      {report.improvement_checklist?.length > 0 && (
        <section className="border border-foreground/10 bg-foreground/[0.02] p-6">
          <h3 className="mb-3 font-display text-lg">Cómo mejorar este análisis</h3>
          <ul className="space-y-2 text-sm">
            {report.improvement_checklist.map((item, i) => (
              <li key={i}>
                <strong className={`uppercase ${PRIORITY_CLASSES[item.priority]}`}>{item.priority}</strong> —{" "}
                {item.title}: {item.action}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Sources */}
      <section>
        <h2 className="mb-4 font-display text-xl">Trazabilidad de fuentes</h2>
        <div className="space-y-2">
          {(report.sources || []).map((s) => (
            <div
              key={s.source + s.request_url}
              className="flex flex-wrap items-center gap-3 border border-foreground/10 bg-foreground/[0.02] px-4 py-3 text-sm"
            >
              <span className="min-w-28 font-mono text-xs font-semibold uppercase">{s.source}</span>
              <span className="font-mono text-xs text-[#64ffda]">
                {s.checksum ? `${s.checksum.slice(0, 8)}…${s.checksum.slice(-6)}` : "—"}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 font-mono text-[11px] ${
                  s.status === "completed" ? "bg-[#64ffda]/15 text-[#64ffda]" : "bg-[#e11d48]/15 text-[#e11d48]"
                }`}
              >
                {s.status}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Ficha */}
      <section className="space-y-4 border border-foreground/10 p-6">
        <h3 className="font-display text-lg">Ficha de oportunidad</h3>
        <div className="flex flex-wrap gap-4">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Segmento
            <input
              value={fichaSegment}
              onChange={(e) => setFichaSegment(e.target.value)}
              maxLength={200}
              className="min-w-56 border border-foreground/20 bg-transparent px-3 py-2 text-sm text-foreground"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Etapa
            <select
              value={fichaStage}
              onChange={(e) => setFichaStage(e.target.value)}
              className="border border-foreground/20 bg-transparent px-3 py-2 text-sm text-foreground"
            >
              {["idea", "concepto", "prototipo", "piloto", "escalamiento"].map((s) => (
                <option key={s} value={s} className="bg-background">
                  {s}
                </option>
              ))}
            </select>
          </label>
        </div>
        {fichaError && <p className="text-sm text-[#e11d48]">{fichaError}</p>}
        {fichaMarkdown ? (
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Ficha generada</span>
              <button
                onClick={handleDownloadFicha}
                className="rounded-full border border-foreground/20 px-3 py-1 text-xs hover:border-foreground/50"
              >
                Descargar .md
              </button>
            </div>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap border border-foreground/10 bg-foreground/[0.02] p-4 font-mono text-xs leading-relaxed text-muted-foreground">
              {fichaMarkdown}
            </pre>
          </div>
        ) : (
          <button
            onClick={handleGenerateFicha}
            disabled={!fichaAvailable || fichaGenerating}
            className="rounded-full bg-[#64ffda] px-5 py-2 text-sm font-medium text-[#0a192f] transition-opacity disabled:opacity-40"
          >
            {fichaGenerating ? "Generando…" : "Generar Ficha"}
          </button>
        )}
      </section>

      {/* Actions */}
      <section className="flex flex-wrap gap-3 border-t border-foreground/10 pt-6">
        <button
          onClick={() => setShowJson((v) => !v)}
          className="rounded-full border border-foreground/20 px-5 py-2 text-sm hover:border-foreground/50"
        >
          {showJson ? "Ocultar JSON" : "Ver JSON"}
        </button>
        <a
          href={reportPdfUrl(report.run_id)}
          target="_blank"
          rel="noreferrer"
          className="rounded-full bg-[#64ffda] px-5 py-2 text-sm font-medium text-[#0a192f]"
        >
          Descargar PDF ejecutivo
        </a>
      </section>
      {showJson && (
        <pre className="max-h-96 overflow-auto whitespace-pre-wrap border border-foreground/10 bg-foreground/[0.02] p-4 font-mono text-xs text-muted-foreground">
          {JSON.stringify(report, null, 2)}
        </pre>
      )}
    </div>
  );
}
