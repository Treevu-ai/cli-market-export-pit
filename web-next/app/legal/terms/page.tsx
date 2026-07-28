"use client";

import { AppHeader } from "@/components/app-header";
import { useLocale } from "@/lib/i18n/locale-context";
import { es } from "@/lib/i18n/dictionaries/es";
import { en } from "@/lib/i18n/dictionaries/en";

const SECTIONS_BY_LOCALE = { es: es.legal.terms.sections, en: en.legal.terms.sections };

export default function TermsPage() {
  const { t, locale } = useLocale();
  const sections = SECTIONS_BY_LOCALE[locale];
  return (
    <>
      <AppHeader />
      <main className="min-h-screen bg-background px-6 py-24 text-foreground">
      <div className="mx-auto max-w-2xl">
        <h1 className="font-display text-4xl">{t("legal.terms.title")}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{t("legal.lastUpdated")}</p>

        <div className="mt-10 space-y-8 text-sm leading-relaxed text-muted-foreground">
          {sections.map((section) => (
            <section key={section.heading}>
              <h2 className="mb-2 font-display text-lg text-foreground">{section.heading}</h2>
              <p>
                {"body" in section ? (
                  section.body
                ) : (
                  <>
                    {section.bodyBefore}
                    <a href={section.link.href} className="text-foreground underline underline-offset-2">
                      {section.link.text}
                    </a>
                    {section.bodyAfter}
                  </>
                )}
              </p>
            </section>
          ))}
        </div>
      </div>
      </main>
    </>
  );
}
