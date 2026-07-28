"use client";

import { useState } from "react";
import { signup } from "@/lib/pit-api";
import { useLocale } from "@/lib/i18n/locale-context";

const PASSWORD_SPECIAL_CHARS = /[!@#$%^&*()_+\-=[\]{}|;:,.<>?/~`"'\\]/;

export function SignupForm() {
  const { t, locale } = useLocale();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function validatePassword(value: string): string | null {
    if (/\s/.test(value)) return t("auth.passwordErrorSpace");
    if (!/[A-Z]/.test(value)) return t("auth.passwordErrorUpper");
    if (!/[a-z]/.test(value)) return t("auth.passwordErrorLower");
    if (!/[0-9]/.test(value)) return t("auth.passwordErrorDigit");
    if (!PASSWORD_SPECIAL_CHARS.test(value)) return t("auth.passwordErrorSpecial");
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const passwordError = validatePassword(password);
    if (passwordError) {
      setError(passwordError);
      return;
    }
    setSubmitting(true);
    try {
      await signup(email, password, locale);
      window.location.href = "/analyze/";
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="font-display text-3xl">{t("auth.signupTitle")}</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {t("auth.signupSubtitle")}
      </p>
      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        <div>
          <label className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted-foreground">
            {t("auth.email")}
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-foreground/20 bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted-foreground">
            {t("auth.passwordMin")}
          </label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-foreground/20 bg-transparent px-3 py-2 text-sm"
          />
          <p className="mt-1 text-xs text-muted-foreground">{t("auth.passwordHint")}</p>
        </div>
        {error && <p className="text-sm text-[#e11d48]">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-full bg-[#64ffda] px-5 py-3 text-sm font-medium text-[#0a192f] transition-opacity disabled:opacity-40"
        >
          {submitting ? t("auth.creatingAccount") : t("auth.createFreeAccount")}
        </button>
      </form>
      <p className="mt-6 text-sm text-muted-foreground">
        {t("auth.haveAccount")}{" "}
        <a href="/login" className="text-[#64ffda] hover:underline">
          {t("auth.signIn")}
        </a>
      </p>
    </div>
  );
}
