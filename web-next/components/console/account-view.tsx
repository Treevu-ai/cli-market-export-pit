"use client";

import { useEffect, useState } from "react";
import { getMe, logout, resendVerificationEmail, type MeResponse } from "@/lib/pit-api";
import { useLocale } from "@/lib/i18n/locale-context";

export function AccountView() {
  const { t } = useLocale();
  const [session, setSession] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [verificationResent, setVerificationResent] = useState(false);

  useEffect(() => {
    getMe()
      .then(setSession)
      .catch(() => setSession(null))
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    await logout();
    window.location.href = "/login";
  }

  async function handleResendVerification() {
    setVerificationResent(false);
    await resendVerificationEmail();
    setVerificationResent(true);
  }

  if (loading) return null;

  if (!session) {
    return (
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 text-center">
        <p className="text-muted-foreground">{t("account.notLoggedIn")}</p>
        <a href="/login" className="mt-4 text-[#64ffda] hover:underline">
          {t("auth.signIn")}
        </a>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg px-6 py-24">
      <h1 className="font-display text-3xl">{t("account.title")}</h1>
      <div className="mt-8 space-y-4 border border-foreground/10 bg-foreground/[0.02] p-6">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">{t("account.email")}</span>
          <span>{session.email}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">{t("account.plan")}</span>
          <span className="capitalize">{session.tier}</span>
        </div>
        {session.tier_expires_at && (
          <p className="text-xs text-muted-foreground">
            {t("account.tierExpiresOn")
              .replace("{tier}", session.tier)
              .replace("{date}", new Date(session.tier_expires_at).toLocaleDateString())}
          </p>
        )}
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">{t("account.usageThisMonth")} ({session.usage.period})</span>
          <span className="font-mono text-[#64ffda]">
            {session.usage.used}
            {session.usage.limit !== null ? ` / ${session.usage.limit}` : ` (${t("account.noLimit")})`}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">{t("account.verificationStatus")}</span>
          <span className={session.email_verified ? "text-[#64ffda]" : "text-[#ffd700]"}>
            {session.email_verified ? t("account.emailVerified") : t("account.emailNotVerified")}
          </span>
        </div>
        {!session.email_verified && (
          <button
            type="button"
            onClick={handleResendVerification}
            className="text-xs text-muted-foreground underline"
          >
            {verificationResent ? t("account.resendVerificationSent") : t("account.resendVerification")}
          </button>
        )}
      </div>
      <div className="mt-6 flex gap-4">
        <a href="/pricing" className="rounded-full bg-[#64ffda] px-5 py-2 text-sm font-medium text-[#0a192f]">
          {t("account.viewPlans")}
        </a>
        <button onClick={handleLogout} className="rounded-full border border-foreground/20 px-5 py-2 text-sm">
          {t("account.logout")}
        </button>
      </div>
    </div>
  );
}
