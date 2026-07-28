"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  fetchAgentsStatus,
  fetchReport,
  generateFicha,
  getMe,
  loadRecentRuns,
  runFullPipeline,
  saveRecentRun,
  MARKET_COVERAGE,
  QuotaExceededError,
  type MeResponse,
  type ReportData,
  type RecentRun,
} from "@/lib/pit-api";
import { ReportView } from "./report-view";
import { useLocale } from "@/lib/i18n/locale-context";
import { ThemeToggle } from "@/components/theme-toggle";
import { LanguageToggle } from "@/components/language-toggle";
import { es } from "@/lib/i18n/dictionaries/es";
import { en } from "@/lib/i18n/dictionaries/en";

const SESSION_BAR_BY_LOCALE = { es: es.console.sessionBar, en: en.console.sessionBar };
const QUOTA_NOTICE_BY_LOCALE = { es: es.console.quotaNotice, en: en.console.quotaNotice };
const MARKETS_BY_LOCALE = { es: es.console.form.markets, en: en.console.form.markets };
const PRESETS_BY_LOCALE = { es: es.console.form.presets, en: en.console.form.presets };

const PRESET_QUERIES = [
  { query: "arándano orgánico", market: "US" },
  { query: "palta hass", market: "US" },
  { query: "cacao alto flavanol", market: "US" },
  { query: "quinua orgánica", market: "EU" },
  { query: "mango kent", market: "US" },
];

export function AnalyzeConsole() {
  const { t, locale } = useLocale();
  const sessionBar = SESSION_BAR_BY_LOCALE[locale];
  const quotaNoticeText = QUOTA_NOTICE_BY_LOCALE[locale];
  const MARKETS = MARKETS_BY_LOCALE[locale];
  const PRESETS = PRESETS_BY_LOCALE[locale];
  const STATUS_LABEL: Record<string, { label: string; className: string }> = {
    idle: { label: t("console.status.idle"), className: "bg-foreground/10 text-muted-foreground" },
    running: { label: t("console.status.running"), className: "bg-[#ffd700]/15 text-[#ffd700]" },
    done: { label: t("console.status.done"), className: "bg-[#64ffda]/15 text-[#64ffda]" },
    error: { label: t("console.status.error"), className: "bg-[#e11d48]/15 text-[#e11d48]" },
  };
  const searchParams = useSearchParams();

  const [query, setQuery] = useState("");
  const [targetMarket, setTargetMarket] = useState("US");
  const [application, setApplication] = useState("alimentos y bebidas funcionales");
  const [limit, setLimit] = useState(10);
  const [hsCode, setHsCode] = useState("");

  const [status, setStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [report, setReport] = useState<ReportData | null>(null);
  const [recentRuns, setRecentRuns] = useState<RecentRun[]>([]);
  const [fichaAvailable, setFichaAvailable] = useState(false);
  const [session, setSession] = useState<MeResponse | null>(null);
  const [sessionChecked, setSessionChecked] = useState(false);
  const [quotaNotice, setQuotaNotice] = useState<QuotaExceededError | null>(null);

  useEffect(() => {
    const q = searchParams.get("query");
    const m = searchParams.get("market");
    if (q) setQuery(q);
    if (m) setTargetMarket(m.toUpperCase());
    setRecentRuns(loadRecentRuns());
    fetchAgentsStatus()
      .then((s) => setFichaAvailable(Boolean(s.ficha_available)))
      .catch(() => setFichaAvailable(false));
    getMe()
      .then((me) => setSession(me))
      .catch(() => setSession(null))
      .finally(() => setSessionChecked(true));
  }, [searchParams]);

  const coverage = useMemo(() => MARKET_COVERAGE[targetMarket], [targetMarket]);

  async function loadRun(runId: string) {
    setErrorMessage("");
    setStatus("running");
    try {
      const data = await fetchReport(runId);
      setReport(data);
      setStatus("done");
    } catch (error) {
      setStatus("error");
      setErrorMessage(error instanceof Error ? error.message : String(error));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMessage("");
    setQuotaNotice(null);
    setStatus("running");
    try {
      const run = await runFullPipeline({
        query: query.trim(),
        target_market: targetMarket,
        application: application.trim(),
        limit: Number(limit) || 10,
        ...(hsCode.trim() ? { hs_code: hsCode.trim() } : {}),
      });
      const data = await fetchReport(run.id);
      setReport(data);
      setStatus("done");
      const updated = saveRecentRun({
        id: data.run_id,
        query: data.query,
        target_market: data.target_market,
        score: data.score?.opportunity_score ?? null,
      });
      setRecentRuns(updated);
      getMe().then(setSession).catch(() => {});
    } catch (error) {
      setStatus("error");
      if (error instanceof QuotaExceededError) {
        setQuotaNotice(error);
      } else {
        setErrorMessage(error instanceof Error ? error.message : String(error));
      }
    }
  }

  async function handleGenerateFicha(segment: string, stage: string) {
    if (!report) return null;
    const result = await generateFicha(report.run_id, { segment, stage });
    return result.dossier_markdown || "";
  }

  const statusInfo = STATUS_LABEL[status];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-foreground/10 bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center justify-between gap-y-2 px-6 py-4 lg:px-12">
          <a href="/" className="flex items-center gap-2">
            <span className="font-display text-xl">CLI MARKET</span>
            <span className="font-mono text-xs text-muted-foreground">PIT</span>
          </a>
          <div className="flex flex-wrap items-center gap-3">
            <span className={`rounded-full px-3 py-1 font-mono text-xs ${statusInfo.className}`}>
              {statusInfo.label}
            </span>
            <a href="https://cli-market-pit-backend.fly.dev/docs" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-foreground">
              {t("common.apiDocs")}
            </a>
            <LanguageToggle />
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1400px] gap-8 px-6 py-10 lg:grid-cols-[360px_1fr] lg:px-12">
        {/* Form column */}
        <aside className="space-y-6">
          {sessionChecked && !session && (
            <div className="border border-foreground/10 bg-foreground/[0.02] p-6 text-sm">
              <h2 className="font-display text-lg">{t("console.inicioSesion.title")}</h2>
              <p className="mt-2 text-muted-foreground">
                {t("console.inicioSesion.description")}
              </p>
              <div className="mt-4 flex gap-3">
                <a href="/signup" className="rounded-full bg-[#64ffda] px-4 py-2 text-xs font-medium text-[#0a192f]">
                  {t("console.inicioSesion.createAccount")}
                </a>
                <a href="/login" className="rounded-full border border-foreground/20 px-4 py-2 text-xs">
                  {t("console.inicioSesion.haveAccount")}
                </a>
              </div>
            </div>
          )}
          {session && (
            <div className="border border-foreground/10 bg-foreground/[0.02] p-4 text-xs text-muted-foreground">
              {sessionBar(
                session.email,
                session.tier,
                session.usage.used,
                session.usage.limit !== null ? `/${session.usage.limit}` : ""
              )}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5 border border-foreground/10 bg-foreground/[0.02] p-6">
            <h2 className="font-display text-lg">{t("console.form.title")}</h2>

            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted-foreground">
                {t("console.form.queryLabel")}
              </label>
              <input
                required
                minLength={3}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t("console.form.queryPlaceholder")}
                className="w-full border border-foreground/20 bg-transparent px-3 py-2 text-sm"
              />
              <div className="mt-2 flex flex-wrap gap-2">
                {PRESETS.map((p, i) => (
                  <button
                    key={p.label}
                    type="button"
                    onClick={() => {
                      setQuery(PRESET_QUERIES[i].query);
                      setTargetMarket(PRESET_QUERIES[i].market);
                    }}
                    className="rounded-full border border-foreground/15 px-3 py-1 text-xs text-muted-foreground hover:border-[#64ffda]/60 hover:text-[#64ffda]"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted-foreground">
                {t("console.form.marketLabel")}
              </label>
              <select
                value={targetMarket}
                onChange={(e) => setTargetMarket(e.target.value)}
                className="w-full border border-foreground/20 bg-transparent px-3 py-2 text-sm"
              >
                {MARKETS.map((m) => (
                  <option key={m.code} value={m.code} className="bg-background">
                    {m.code} — {m.name}
                  </option>
                ))}
              </select>
              <p
                className={`mt-2 text-xs ${
                  coverage?.tier === "strong"
                    ? "text-[#64ffda]"
                    : coverage?.tier === "partial"
                      ? "text-[#ffd700]"
                      : "text-muted-foreground"
                }`}
              >
                {coverage ? `● ${coverage.note}` : t("console.form.coverageUnmeasured")}
              </p>
            </div>

            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted-foreground">
                {t("console.form.applicationLabel")}
              </label>
              <input
                value={application}
                onChange={(e) => setApplication(e.target.value)}
                className="w-full border border-foreground/20 bg-transparent px-3 py-2 text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted-foreground">
                  {t("console.form.limitLabel")}
                </label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  className="w-full border border-foreground/20 bg-transparent px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted-foreground">
                  {t("console.form.hsCodeLabel")}
                </label>
                <input
                  value={hsCode}
                  onChange={(e) => setHsCode(e.target.value)}
                  placeholder="081040"
                  className="w-full border border-foreground/20 bg-transparent px-3 py-2 text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={status === "running" || (sessionChecked && !session)}
              className="w-full rounded-full bg-[#64ffda] px-5 py-3 text-sm font-medium text-[#0a192f] transition-opacity disabled:opacity-40"
            >
              {status === "running" ? t("console.form.submitRunning") : t("console.form.submitIdle")}
            </button>
          </form>

          {recentRuns.length > 0 && (
            <div className="border border-foreground/10 bg-foreground/[0.02] p-6">
              <h3 className="mb-3 font-mono text-xs uppercase tracking-wide text-muted-foreground">
                {t("console.recentRuns")}
              </h3>
              <div className="space-y-2">
                {recentRuns.map((run) => (
                  <button
                    key={run.id}
                    onClick={() => loadRun(run.id)}
                    className="flex w-full items-center justify-between border border-foreground/10 px-3 py-2 text-left text-sm hover:border-[#64ffda]/50"
                  >
                    <span className="truncate">
                      {run.query} · {run.target_market}
                    </span>
                    <span className="font-mono text-xs text-[#64ffda]">{run.score ?? "—"}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Results column */}
        <main>
          {quotaNotice && (
            <div className="mb-6 border border-[#ffd700]/30 bg-[#ffd700]/10 p-4 text-sm text-[#ffd700]">
              {quotaNoticeText(quotaNotice.tier, quotaNotice.limit ?? 0)}{" "}
              <a href={quotaNotice.upgradeUrl} className="underline">
                {t("console.viewPlans")}
              </a>
            </div>
          )}
          {errorMessage && (
            <div className="mb-6 border border-[#e11d48]/30 bg-[#e11d48]/10 p-4 text-sm text-[#e11d48]">
              {errorMessage}
            </div>
          )}
          {report ? (
            <ReportView report={report} fichaAvailable={fichaAvailable} onGenerateFicha={handleGenerateFicha} />
          ) : (
            <div className="border border-dashed border-foreground/15 p-16 text-center text-muted-foreground">
              <p className="font-medium">{t("console.noResults")}</p>
              <p className="mt-1 text-sm">{t("console.noResultsDetail")}</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
