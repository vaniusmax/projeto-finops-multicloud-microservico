"use client";

import { useEffect, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { KPIStatCard } from "@/components/dashboard/KPIStatCard";
import { CostExplorerBreakdownCard } from "@/components/cost-explorer/CostExplorerBreakdownCard";
import { CostExplorerInsightPanel } from "@/components/cost-explorer/CostExplorerInsightPanel";
import { CostExplorerTrendCard } from "@/components/cost-explorer/CostExplorerTrendCard";
import { CostExplorerVarianceTable } from "@/components/cost-explorer/CostExplorerVarianceTable";
import { InfoHint } from "@/components/ui/info-hint";
import { useAppContext } from "@/contexts/AppContext";
import {
  useCostExplorerBreakdownQuery,
  useCostExplorerInsightsQuery,
  useCostExplorerSnapshotQuery,
  useCostExplorerTrendQuery,
} from "@/hooks/use-finops-queries";
import { formatCompactMoney, formatDateLabel } from "@/lib/format";
import { mergeSearchParams } from "@/lib/query/search-params";

type GroupBy = "service" | "account";

export function CostExplorerModule() {
  const { filters } = useAppContext();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const groupBy = (searchParams.get("groupBy") === "account" ? "account" : "service") as GroupBy;
  const snapshot = useCostExplorerSnapshotQuery(filters, groupBy);
  const breakdown = useCostExplorerBreakdownQuery(filters, groupBy);
  const selectedItem = useMemo(() => {
    const requested = searchParams.get("selected");
    if (requested) return requested;
    return breakdown.data?.[0]?.label ?? null;
  }, [breakdown.data, searchParams]);
  const trend = useCostExplorerTrendQuery(filters, groupBy, selectedItem, Boolean(selectedItem));
  const insights = useCostExplorerInsightsQuery(filters, groupBy, selectedItem, Boolean(selectedItem));

  useEffect(() => {
    if (!searchParams.get("selected") && breakdown.data?.[0]?.label) {
      const params = mergeSearchParams(new URLSearchParams(searchParams.toString()), filters, {
        groupBy,
        selected: breakdown.data[0].label,
      });
      router.replace(`${pathname}?${params.toString()}`);
    }
  }, [breakdown.data, filters, groupBy, pathname, router, searchParams]);

  function updateExplorerParams(extras: Record<string, string | null>) {
    const params = mergeSearchParams(new URLSearchParams(searchParams.toString()), filters, extras);
    router.push(`${pathname}?${params.toString()}`);
  }

  const kpis = snapshot.data;

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumbs items={[{ label: filters.cloud.toUpperCase() }, { label: "Cost Explorer" }]} />
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Cost explorer</h1>
        <p className="mt-1 text-sm text-slate-500">Investigacao guiada com snapshot deterministico, variancia e camada interpretativa opcional.</p>
      </div>

      <section className="grid gap-4 xl:grid-cols-5">
        <KPIStatCard
          title="Total do periodo"
          value={kpis?.totalPeriod}
          currency={filters.currency}
          delta={kpis?.deltaPeriodPct}
          tone="hero"
          valueType="compact-money"
          subtitle="Recorte atual"
          hint="Soma de todos os custos do período selecionado, já respeitando cloud, moeda e filtros ativos."
        />
        <KPIStatCard
          title="Top 1 concentration"
          value={kpis?.top1SharePct}
          currency={filters.currency}
          valueType="pct"
          subtitle="Participacao do item lider"
          hint={`Percentual do custo total concentrado no maior item do agrupamento atual (${groupBy === "service" ? "serviço" : "conta"}). Quanto maior esse número, mais dependente o recorte está de um único item.`}
        />
        <KPIStatCard
          title="Top 3 concentration"
          value={kpis?.top3SharePct}
          currency={filters.currency}
          valueType="pct"
          subtitle="Share acumulado dos tres maiores"
          hint={`Percentual somado dos três maiores itens do agrupamento atual (${groupBy === "service" ? "serviço" : "conta"}). Ajuda a medir se o custo está pulverizado ou concentrado em poucos itens.`}
        />
        <KPIStatCard
          title="Largest service"
          value={kpis?.largestService?.value}
          currency={filters.currency}
          delta={kpis?.largestService?.deltaPct}
          valueType="compact-money"
          subtitle={kpis?.largestService?.label ?? "Sem servico lider"}
          hint="Serviço com maior custo absoluto dentro do período selecionado. O delta ao lado mostra como ele variou versus o período anterior equivalente."
        />
        <KPIStatCard
          title="Peak day"
          value={kpis?.peakDay.amount}
          currency={filters.currency}
          valueType="compact-money"
          subtitle={kpis?.peakDay?.date ? formatDateLabel(kpis.peakDay.date) : "Sem pico"}
          hint="Dia com maior gasto dentro do recorte atual. Esse card ajuda a localizar picos operacionais ou eventos de consumo fora do padrão."
        />
      </section>

      <CostExplorerInsightPanel
        data={insights.data}
        isLoading={insights.isLoading}
        onSelectDrilldown={(value) => updateExplorerParams({ selected: value })}
      />

      <section className="grid gap-4 xl:grid-cols-12">
        <div className="xl:col-span-7">
          <CostExplorerBreakdownCard
            data={breakdown.data}
            isLoading={breakdown.isLoading}
            currency={filters.currency}
            groupBy={groupBy}
            selectedItem={selectedItem}
            onGroupByChange={(value) => updateExplorerParams({ groupBy: value, selected: null })}
            onSelectItem={(item) => updateExplorerParams({ selected: item })}
          />
        </div>

        <div className="xl:col-span-5 space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-[linear-gradient(145deg,#ffffff_0%,#f0fdf4_100%)] p-5 shadow-soft">
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700">Focus item</p>
              <InfoHint content="Item atualmente selecionado no breakdown. Ele passa a ser o centro da análise de tendência, recomendações e drilldowns sugeridos." />
            </div>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">{selectedItem ?? "Aguardando selecao"}</h2>
            <p className="mt-2 text-sm text-slate-500">
              Clique em um item do breakdown para ancorar tendencia, recomendações e próximos drilldowns.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-emerald-100 bg-white p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Group by</p>
                <p className="mt-2 text-sm font-medium text-slate-900">{groupBy}</p>
              </div>
              <div className="rounded-2xl border border-emerald-100 bg-white p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Largest account</p>
                <p className="mt-2 text-sm font-medium text-slate-900">{kpis?.largestAccount?.label ?? "n/d"}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {kpis?.largestAccount ? formatCompactMoney(kpis.largestAccount.value, filters.currency) : "Sem destaque"}
                </p>
              </div>
            </div>
          </div>

          <CostExplorerTrendCard
            data={trend.data}
            isLoading={trend.isLoading}
            currency={filters.currency}
            selectedItem={selectedItem}
          />
        </div>
      </section>

      <CostExplorerVarianceTable data={breakdown.data} isLoading={breakdown.isLoading} currency={filters.currency} />
    </div>
  );
}
