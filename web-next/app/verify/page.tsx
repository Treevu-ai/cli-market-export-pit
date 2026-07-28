import { Suspense } from "react";
import { AppHeader } from "@/components/app-header";
import { VerifyView } from "@/components/console/verify-view";

export default function VerifyPage() {
  return (
    <>
      <AppHeader />
      <Suspense fallback={null}>
        <VerifyView />
      </Suspense>
    </>
  );
}
