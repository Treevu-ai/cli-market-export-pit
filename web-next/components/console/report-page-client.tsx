"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { fetchAgentsStatus, fetchReport, generateFicha, type ReportData } from "@/lib/pit-api";
import { ReportView } from "./report-view";
import { useLocale } from "@/lib/i18n/locale-context";
import { ThemeToggle } from "@/components/theme-toggle";
import { LanguageToggle } from "@/components/language-toggle";

export function ReportPageClient() {
  const { t } = useLocale();
  const searchParams = useSearchParams();
  const runId = searchParams.get("run_id");

  const [report, setReport] = useState<ReportData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fichaAvailable, setFichaAvailable] = useState(false);

  useEffect(() => {
    fetchAgentsStatus()
      .then((s) => setFichaAvailable(Boolean(s.ficha_available)))
      .catch(() => setFichaAvailable(false));
  }, []);

  useEffect(() => {
    if (!runId) return;
    fetchReport(runId)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [runId]);

  async function handleGenerateFicha(segment: string, stage: string) {
    if (!report) return null;
    const result = await generateFicha(report.run_id, { segment, stage });
    return result.dossier_markdown || "";
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-foreground/10 bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center justify-between gap-y-2 px-6 py-4 lg:px-12">
          <a href="/" className="flex items-center gap-2">
            <span className="font-display text-xl">CLI MARKET</span>
            <span className="font-mono text-xs text-muted-foreground">PIT</span>
          </a>
          <div className="flex flex-wrap items-center gap-4">
            <a href="/analyze/" className="text-sm text-muted-foreground hover:text-foreground">
              {t("console.backToConsole")}
            </a>
            <LanguageToggle />
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1000px] px-6 py-10 lg:px-12">
        {!runId && (
          <div className="border border-dashed border-foreground/15 p-16 text-center text-muted-foreground">
            <p className="font-medium">{t("console.noRunId")}</p>
            <p className="mt-1 text-sm">
              {t("console.noRunIdDetail")}
            </p>
          </div>
        )}
        {error && <div className="border border-[#e11d48]/30 bg-[#e11d48]/10 p-4 text-sm text-[#e11d48]">{error}</div>}
        {report && <ReportView report={report} fichaAvailable={fichaAvailable} onGenerateFicha={handleGenerateFicha} />}
      </div>
    </div>
  );
}
