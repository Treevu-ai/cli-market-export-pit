"use client";

import { EvidenceCard, type Trend } from "./evidence-card";
import { useLocale } from "@/lib/i18n/locale-context";

type Props = {
  summaries: Record<string, any>;
};

function asTrend(value: unknown): Trend | undefined {
  return value === "growing" || value === "declining" || value === "stable" ? value : undefined;
}

export function EvidenceGrid({ summaries }: Props) {
  const { t } = useLocale();

  const openalex = summaries.openalex_aggregation;
  const epoOps = summaries.epo_ops_aggregation;
  const gdelt = summaries.gdelt_aggregation;
  const comtrade = summaries.comtrade_aggregation;
  const techscout = summaries.techscout_aggregation;
  const climatiq = summaries.climatiq_aggregation;
  const bcrp = summaries.bcrp_aggregation;
  const bcrpSeries = bcrp?.series?.[0];

  const cards = [
    {
      key: "science",
      title: t("report.domainLabels.science"),
      stat: openalex?.top_topics?.length
        ? { value: openalex.top_topics.length, label: t("report.evidence.science.topicsFound") }
        : undefined,
      chips: openalex?.top_topics,
      emptyLabel: t("report.evidence.science.empty"),
    },
    {
      key: "patent",
      title: t("report.domainLabels.patent"),
      stat: epoOps?.patents_count != null
        ? { value: epoOps.patents_count, label: t("report.evidence.patent.count") }
        : undefined,
      trend: asTrend(epoOps?.filing_trend),
      chips: epoOps?.top_assignees,
      emptyLabel: t("report.evidence.patent.empty"),
    },
    {
      key: "trend",
      title: t("report.domainLabels.trend"),
      stat: gdelt?.news_volume != null
        ? { value: gdelt.news_volume, label: t("report.evidence.trend.newsVolume") }
        : undefined,
      trend: asTrend(gdelt?.trend),
      chips: gdelt?.top_domains,
      emptyLabel: t("report.evidence.trend.empty"),
    },
    {
      key: "trade",
      title: t("report.domainLabels.trade"),
      stat: comtrade?.trade_records_count != null
        ? { value: comtrade.trade_records_count, label: t("report.evidence.trade.records") }
        : undefined,
      trend: asTrend(comtrade?.trend),
      chips: comtrade?.top_partners,
      emptyLabel: t("report.evidence.trade.empty"),
    },
    {
      key: "technology_scout",
      title: t("report.domainLabels.technology_scout"),
      stat: techscout?.total_projects != null
        ? { value: techscout.total_projects, label: t("report.evidence.techscout.count") }
        : undefined,
      chips: (techscout?.sources || []).map((s: any) => `${s.source}: ${s.project_count}`),
      emptyLabel: t("report.evidence.techscout.empty"),
    },
    {
      key: "sustainability",
      title: t("report.domainLabels.sustainability"),
      stat: climatiq?.activity_count != null
        ? { value: climatiq.activity_count, label: t("report.evidence.sustainability.count") }
        : undefined,
      chips: climatiq?.top_categories,
      emptyLabel: t("report.evidence.sustainability.empty"),
    },
    {
      key: "macro",
      title: t("report.evidence.macro.title"),
      stat: bcrpSeries
        ? { value: bcrpSeries.latest_value, label: `${bcrpSeries.name} (${bcrpSeries.latest_period})` }
        : undefined,
      emptyLabel: t("report.evidence.macro.empty"),
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map(({ key, ...card }) => (
        <EvidenceCard key={key} {...card} />
      ))}
    </div>
  );
}
