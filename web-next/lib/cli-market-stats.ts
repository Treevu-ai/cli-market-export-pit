export interface HeroStats {
  skus: string;
  priceSnapshots: string;
  countries: string;
}

const FALLBACK_STATS: HeroStats = {
  skus: "130K+",
  priceSnapshots: "149K+",
  countries: "21",
};

function formatCompact(value: number): string {
  if (value >= 1000) {
    return `${Math.floor(value / 1000)}K+`;
  }
  return String(value);
}

interface AnalyticsStatsResponse {
  total_price_snapshots?: number;
  unique_products_tracked?: number;
}

interface CoverageMatrixResponse {
  countries?: string[];
}

// Runs server-side on each request (revalidated every 5 min) — the API key
// never reaches the client bundle, only the resulting formatted numbers do.
export async function getCliMarketHeroStats(): Promise<HeroStats> {
  const apiKey = process.env.CLIMARKET_API_KEY;
  const baseUrl = process.env.CLIMARKET_API_URL ?? "https://cli-market-api.fly.dev";

  if (!apiKey) {
    return FALLBACK_STATS;
  }

  try {
    const headers = { Authorization: `Bearer ${apiKey}` };
    const [statsRes, coverageRes] = await Promise.all([
      fetch(`${baseUrl}/analytics/stats`, { headers, next: { revalidate: 300 } }),
      fetch(`${baseUrl}/v1/coverage/matrix`, { headers, next: { revalidate: 300 } }),
    ]);

    if (!statsRes.ok || !coverageRes.ok) {
      return FALLBACK_STATS;
    }

    const stats: AnalyticsStatsResponse = await statsRes.json();
    const coverage: CoverageMatrixResponse = await coverageRes.json();

    const countryCount = coverage.countries?.filter((code) => code !== "??").length;

    return {
      skus:
        typeof stats.unique_products_tracked === "number"
          ? formatCompact(stats.unique_products_tracked)
          : FALLBACK_STATS.skus,
      priceSnapshots:
        typeof stats.total_price_snapshots === "number"
          ? formatCompact(stats.total_price_snapshots)
          : FALLBACK_STATS.priceSnapshots,
      countries: countryCount ? String(countryCount) : FALLBACK_STATS.countries,
    };
  } catch {
    return FALLBACK_STATS;
  }
}
