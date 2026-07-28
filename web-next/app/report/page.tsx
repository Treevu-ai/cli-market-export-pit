import { Suspense } from "react";
import { ReportPageClient } from "@/components/console/report-page-client";

export default function ReportPage() {
  return (
    <Suspense fallback={null}>
      <ReportPageClient />
    </Suspense>
  );
}
