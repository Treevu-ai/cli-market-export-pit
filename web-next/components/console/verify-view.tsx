"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { verifyEmail } from "@/lib/pit-api";
import { useLocale } from "@/lib/i18n/locale-context";

export function VerifyView() {
  const { t } = useLocale();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      return;
    }
    verifyEmail(token)
      .then(() => setStatus("success"))
      .catch(() => setStatus("error"));
  }, [searchParams]);

  if (status === "loading") {
    return (
      <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 text-center">
        <p className="text-muted-foreground">{t("auth.verifyPageVerifying")}</p>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 text-center">
        <h1 className="font-display text-3xl">{t("auth.verifyPageSuccessTitle")}</h1>
        <p className="mt-2 text-muted-foreground">{t("auth.verifyPageSuccessBody")}</p>
        <a
          href="/analyze/"
          className="mt-6 rounded-full bg-[#64ffda] px-5 py-3 text-sm font-medium text-[#0a192f]"
        >
          {t("auth.verifyPageSuccessCta")}
        </a>
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 text-center">
      <h1 className="font-display text-3xl">{t("auth.verifyPageErrorTitle")}</h1>
      <p className="mt-2 text-muted-foreground">{t("auth.verifyPageErrorBody")}</p>
      <a href="/login" className="mt-6 rounded-full border border-foreground/20 px-5 py-3 text-sm">
        {t("auth.verifyPageErrorCta")}
      </a>
    </div>
  );
}
