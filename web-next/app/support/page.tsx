"use client";

import { AppHeader } from "@/components/app-header";
import { useLocale } from "@/lib/i18n/locale-context";

export default function SupportPage() {
  const { t } = useLocale();
  return (
    <>
      <AppHeader />
      <main className="min-h-screen bg-background px-6 py-24 text-foreground">
      <div className="mx-auto max-w-2xl">
        <h1 className="font-display text-4xl">{t("support.title")}</h1>
        <p className="mt-4 text-muted-foreground">
          {t("support.intro")}
        </p>

        <div className="mt-10 space-y-6">
          <div className="border border-foreground/10 bg-foreground/[0.02] p-6">
            <h2 className="font-mono text-xs uppercase tracking-wide text-muted-foreground">{t("support.emailLabel")}</h2>
            <a href="mailto:hello@cli-market.dev" className="mt-2 block text-lg text-[#64ffda] hover:underline">
              hello@cli-market.dev
            </a>
          </div>

          <div className="border border-foreground/10 bg-foreground/[0.02] p-6">
            <h2 className="font-mono text-xs uppercase tracking-wide text-muted-foreground">{t("support.apiDocsLabel")}</h2>
            <a
              href="https://cli-market-pit-backend.fly.dev/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 block text-lg text-[#64ffda] hover:underline"
            >
              cli-market-pit-backend.fly.dev/docs
            </a>
          </div>

          <div className="border border-foreground/10 bg-foreground/[0.02] p-6">
            <h2 className="font-mono text-xs uppercase tracking-wide text-muted-foreground">{t("support.enterpriseLabel")}</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {t("support.enterpriseText")}{" "}
              <a href="/pricing" className="text-[#64ffda] hover:underline">
                {t("support.pricingLink")}
              </a>{" "}
              {t("support.orWriteUs")}
            </p>
          </div>
        </div>
      </div>
      </main>
    </>
  );
}
