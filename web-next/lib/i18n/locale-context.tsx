"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { es } from "./dictionaries/es";
import { en } from "./dictionaries/en";

export type Locale = "es" | "en";

const DICTIONARIES: Record<Locale, Record<string, unknown>> = { es, en };
const LOCALE_KEY = "pit_locale";

function lookup(dict: Record<string, unknown>, path: string): unknown {
  return path.split(".").reduce<unknown>((acc, part) => {
    if (acc && typeof acc === "object" && part in (acc as Record<string, unknown>)) {
      return (acc as Record<string, unknown>)[part];
    }
    return undefined;
  }, dict);
}

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
  tList: (key: string) => string[];
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("es");

  useEffect(() => {
    const stored = window.localStorage.getItem(LOCALE_KEY);
    if (stored === "es" || stored === "en") {
      setLocaleState(stored);
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  function setLocale(next: Locale) {
    setLocaleState(next);
    window.localStorage.setItem(LOCALE_KEY, next);
  }

  function t(key: string): string {
    const value = lookup(DICTIONARIES[locale], key) ?? lookup(DICTIONARIES.es, key);
    return typeof value === "string" ? value : key;
  }

  function tList(key: string): string[] {
    const value = lookup(DICTIONARIES[locale], key) ?? lookup(DICTIONARIES.es, key);
    return Array.isArray(value) ? (value as string[]) : [];
  }

  return <LocaleContext.Provider value={{ locale, setLocale, t, tList }}>{children}</LocaleContext.Provider>;
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error("useLocale must be used within a LocaleProvider");
  return ctx;
}
