"use client";

import { useState } from "react";
import {
  RECOMMENDATION_LABELS,
  reportPdfUrl,
  type ReportData,
} from "@/lib/pit-api";
import { ScoreGauge } from "./score-gauge";
import { DomainGrid } from "./domain-grid";
import { useLocale } from "@/lib/i18n/locale-context";

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

const COMPLEMENTARY_KEY_TO_I18N: Record<string, string> = {
  comtrade_aggregation: "comtrade",
  climatiq_aggregation: "climatiq",
  techscout_aggregation: "techscout",
  bcrp_aggregation: "bcrp",
};

type Props = {
  report: ReportData;
  fichaAvailable: boolean;
  onGenerateFicha: (segment: string, stage: string) => Promise<string | null>;
};

function buildComplementaryDetail(key: string, data: any, locale: "es" | "en"): string {
  if (key === "comtrade_aggregation") {
    return locale === "es"
      ? `${data.trade_records_count ?? 0} registros · tendencia ${data.trend ?? "—"} (Comtrade)`
      : `${data.trade_records_count ?? 0} records · trend ${data.trend ?? "—"} (Comtrade)`;
  }
  if (key === "climatiq_aggregation") {
    if (data?.activity_count == null) return locale === "es" ? "Sin datos de carbono" : "No carbon data";
    return locale === "es"
      ? `${data.activity_count} actividades de huella (Climatiq)`
      : `${data.activity_count} footprint activities (Climatiq)`;
  }
  if (key === "techscout_aggregation") {
    if (data?.total_projects == null) return locale === "es" ? "Sin proyectos de I+D" : "No R&D projects";
    return locale === "es"
      ? `${data.total_projects} proyectos (CORDIS, NIH, NSF)`
      : `${data.total_projects} projects (CORDIS, NIH, NSF)`;
  }
  if (key === "bcrp_aggregation") {
    const series = data?.series?.[0];
    if (!series) return locale === "es" ? "Sin datos macro del BCRP" : "No BCRP macro data";
    return `${series.name}: ${series.latest_value} (${series.latest_period})`;
  }
  return "";
}

export function ReportView({ report, fichaAvailable, onGenerateFicha }: Props) {
  const { t, locale } = useLocale();
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

  const complementary = Object.entries(COMPLEMENTARY_KEY_TO_I18N)
    .map(([key, i18nKey]) => [key, i18nKey, summaries[key]] as const)
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
              {t("report.coverage")}: <strong className="text-foreground">{score.coverage_factor ?? "—"}</strong> ·{" "}
              {score.score_version}
            </p>
          </div>
        </div>
      </section>

      {/* Domain grid */}
      <section>
        <h2 className="mb-4 font-display text-xl">{t("report.domains")}</h2>
        <DomainGrid dimensions={score.dimensions || {}} />
      </section>

      {/* Regulatory + commerce */}
      <section className="grid gap-4 md:grid-cols-2">
        <div className="border border-foreground/10 p-6">
          <h3 className="mb-4 font-display text-lg">{t("report.regulatoryHub")}</h3>
          {regulatory && regulatory.total_records ? (
            <>
              <p className="mb-3 text-sm text-muted-foreground">
                <strong className="text-foreground">{regulatory.total_records}</strong> {t("report.regulatoryFound")}
              </p>
              {(regulatory.sources || []).map((s: any) => (
                <div key={s.source} className="flex justify-between border-b border-foreground/10 py-2 text-sm last:border-b-0">
                  <span>{s.source}</span>
                  <span className="font-mono text-[#64ffda]">{s.record_count}</span>
                </div>
              ))}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">{t("report.noRegulatory")}</p>
          )}
        </div>
        <div className="border border-foreground/10 p-6">
          <h3 className="mb-4 font-display text-lg">{t("report.commerceBenchmarks")}</h3>
          {commerce && commerce.price_max != null ? (
            <>
              {[
                { label: t("report.priceMin"), value: commerce.price_min },
                { label: t("report.priceAvg"), value: commerce.price_avg },
                { label: t("report.priceMax"), value: commerce.price_max },
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
                {commerce.stores_compared ?? 0} {t("report.storesCompared")} · {commerce.shelf_products_count ?? 0} {t("report.shelfProducts")}.
              </p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">{t("report.noCommerce")}</p>
          )}
        </div>
      </section>

      {/* Complementary */}
      <section>
        <h2 className="mb-4 font-display text-xl">{t("report.complementaryEvidence")}</h2>
        {complementary.length ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {complementary.map(([key, i18nKey, data]) => (
              <div key={key} className="border border-foreground/10 bg-foreground/[0.02] p-4">
                <strong className="mb-1 block font-display text-sm">{t(`report.complementaryKeys.${i18nKey}`)}</strong>
                <p className="text-sm text-muted-foreground">{buildComplementaryDetail(key, data, locale)}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">{t("report.noComplementary")}</p>
        )}
      </section>

      {/* Checklist */}
      {report.improvement_checklist?.length > 0 && (
        <section className="border border-foreground/10 bg-foreground/[0.02] p-6">
          <h3 className="mb-3 font-display text-lg">{t("report.improveTitle")}</h3>
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
        <h2 className="mb-4 font-display text-xl">{t("report.sourcesTraceability")}</h2>
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
        <h3 className="font-display text-lg">{t("report.fichaTitle")}</h3>
        <div className="flex flex-wrap gap-4">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("report.segment")}
            <input
              value={fichaSegment}
              onChange={(e) => setFichaSegment(e.target.value)}
              maxLength={200}
              className="min-w-56 border border-foreground/20 bg-transparent px-3 py-2 text-sm text-foreground"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("report.stage")}
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
              <span className="text-xs text-muted-foreground">{t("report.fichaGenerated")}</span>
              <button
                onClick={handleDownloadFicha}
                className="rounded-full border border-foreground/20 px-3 py-1 text-xs hover:border-foreground/50"
              >
                {t("report.downloadMd")}
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
            {fichaGenerating ? t("report.generatingFicha") : t("report.generateFicha")}
          </button>
        )}
      </section>

      {/* Actions */}
      <section className="flex flex-wrap gap-3 border-t border-foreground/10 pt-6">
        <button
          onClick={() => setShowJson((v) => !v)}
          className="rounded-full border border-foreground/20 px-5 py-2 text-sm hover:border-foreground/50"
        >
          {showJson ? t("report.hideJson") : t("report.showJson")}
        </button>
        <a
          href={reportPdfUrl(report.run_id)}
          target="_blank"
          rel="noreferrer"
          className="rounded-full bg-[#64ffda] px-5 py-2 text-sm font-medium text-[#0a192f]"
        >
          {t("report.downloadPdf")}
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
