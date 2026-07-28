import { Suspense } from "react";
import { AnalyzeConsole } from "@/components/console/analyze-console";

export default function AnalyzePage() {
  return (
    <Suspense fallback={null}>
      <AnalyzeConsole />
    </Suspense>
  );
}
