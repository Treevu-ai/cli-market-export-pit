"use client";

import { useLocale } from "@/lib/i18n/locale-context";

export function LanguageToggle() {
  const { locale, setLocale } = useLocale();

  return (
    <div className="inline-flex items-center rounded-full border border-foreground/15 p-0.5 text-xs font-mono">
      <button
        type="button"
        onClick={() => setLocale("es")}
        aria-pressed={locale === "es"}
        className={`rounded-full px-2 py-1 transition-colors ${
          locale === "es" ? "bg-foreground text-background" : "text-foreground/60 hover:text-foreground"
        }`}
      >
        ES
      </button>
      <button
        type="button"
        onClick={() => setLocale("en")}
        aria-pressed={locale === "en"}
        className={`rounded-full px-2 py-1 transition-colors ${
          locale === "en" ? "bg-foreground text-background" : "text-foreground/60 hover:text-foreground"
        }`}
      >
        EN
      </button>
    </div>
  );
}
