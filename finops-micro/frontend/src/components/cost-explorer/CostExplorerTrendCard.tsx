"use client";

import { EmptyState } from "@/components/dashboard/EmptyState";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { LineChartDaily } from "@/components/charts/LineChartDaily";
import type { Currency } from "@/lib/format";
import type { CostExplorerTrendResponse, DailyResponse } from "@/lib/schemas/finops";

type CostExplorerTrendCardProps = {
  data?: CostExplorerTrendResponse;
  isLoading: boolean;
  currency: Currency;
  selectedItem: string | null;
};

export function CostExplorerTrendCard({ data, isLoading, currency, selectedItem }: CostExplorerTrendCardProps) {
  const chartData: DailyResponse =
    data?.map((item) => ({
      date: item.date,
      total: item.total,
      byService: {
        [selectedItem ?? "Focus"]: item.selected,
        Others: item.others,
      },
    })) ?? [];

  return (
    <SectionCard
      title="Trend focus"
      description={`Leitura diaria do item ${selectedItem ?? "lider"} contra o restante do recorte.`}
      hint="Compara a evolução diária do item em foco com o restante do custo do período. Serve para identificar se o comportamento do item selecionado explica os picos ou a variação do recorte."
    >
      {isLoading ? (
        <div className="h-[360px] animate-pulse rounded-2xl bg-slate-100" />
      ) : !data || data.length === 0 ? (
        <EmptyState title="Sem serie temporal" description="Nao ha dados diarios suficientes para exibir a tendencia." />
      ) : (
        <LineChartDaily data={chartData} currency={currency} title="Evolucao do foco vs restante" />
      )}
    </SectionCard>
  );
}
