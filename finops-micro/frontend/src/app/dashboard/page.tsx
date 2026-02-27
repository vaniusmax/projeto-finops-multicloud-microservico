"use client";

import { useMemo, useState } from "react";
import { BarChart3, CalendarRange, Wallet } from "lucide-react";
import { useSearchParams } from "next/navigation";

import { AiAssistant } from "@/components/ai/AiAssistant";
import { BarChartCost } from "@/components/charts/BarChartCost";
import { LineChartDaily } from "@/components/charts/LineChartDaily";
import { WeeklyDrilldownModal } from "@/components/drilldown/WeeklyDrilldownModal";
import { KpiCard } from "@/components/kpi/KpiCard";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { LinkedAccountTable } from "@/components/tables/LinkedAccountTable";
import { TopServicesTable } from "@/components/tables/TopServicesTable";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardFilters } from "@/hooks/use-dashboard-filters";
import {
  useDailyQuery,
  useFilterOptionsQuery,
  useSummaryQuery,
  useTopAccountsQuery,
  useTopServicesQuery,
} from "@/hooks/use-finops-queries";
import { toSearchParams } from "@/lib/query/search-params";

export default function DashboardPage() {
  const [drilldownOpen, setDrilldownOpen] = useState(false);
  const searchParams = useSearchParams();
  const tab = searchParams.get("tab") === "ai" ? "ai" : "dashboard";

  const { filters, updateFilters } = useDashboardFilters();
  const chartFilters = { ...filters, topN: 10 };
  const month = filters.from.slice(0, 7);

  const summary = useSummaryQuery(filters);
  const daily = useDailyQuery(chartFilters);
  const topServices = useTopServicesQuery(chartFilters);
  const topAccounts = useTopAccountsQuery(chartFilters);
  const filterOptions = useFilterOptionsQuery(filters.cloud, month);

  const filtersQuery = useMemo(() => toSearchParams(filters).toString(), [filters]);

  const isLoading =
    summary.isLoading || daily.isLoading || topServices.isLoading || topAccounts.isLoading || filterOptions.isLoading;

  return (
    <div className="flex min-h-screen bg-app-bg">
      <Sidebar
        filters={filters}
        services={filterOptions.data?.services ?? []}
        accounts={filterOptions.data?.accounts ?? []}
        onFiltersChange={updateFilters}
      />

      <main className="w-full p-4 md:ml-[300px] md:p-8">
        <Header cloud={filters.cloud} activeTab={tab} filtersQuery={filtersQuery} />

        <p className="mb-6 text-sm text-slate-500">
          Nuvem: {filters.cloud.toUpperCase()} | Período: {filters.from} a {filters.to} | Moeda: {filters.currency} | Top N: 10
        </p>

        {tab === "ai" ? <AiAssistant filters={filters} /> : null}

        {tab === "dashboard" ? (
          <>
            <section>
              <h2 className="mb-4 text-3xl font-bold">VISÃO GERAL</h2>
              {isLoading || !summary.data ? (
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
                  {Array.from({ length: 6 }).map((_, index) => (
                    <Skeleton key={index} className="h-[130px]" />
                  ))}
                </div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
                  <KpiCard
                    title="META CONSUMO ANUAL"
                    value={summary.data.budgetYear}
                    currency={filters.currency}
                    valueType="compact-money"
                  />
                  <KpiCard
                    title="META CONSUMO MÊS"
                    value={summary.data.budgetMonth}
                    currency={filters.currency}
                    valueType="compact-money"
                  />
                  <KpiCard title="CONSUMO TOTAL DO ANO" value={summary.data.yearTotal} currency={filters.currency} valueType="compact-money" />
                  <KpiCard title="CONSUMO DO MÊS" value={summary.data.monthTotal} currency={filters.currency} valueType="compact-money" selected />
                  <KpiCard
                    title="CONSUMO SEMANAL"
                    value={summary.data.totalWeek}
                    currency={filters.currency}
                    delta={summary.data.deltaWeek}
                    valueType="compact-money"
                    selected
                    onClick={() => setDrilldownOpen(true)}
                  />
                  <KpiCard title="COTAÇÃO USD" value={summary.data.usdRate} currency={filters.currency} valueType="number" />
                </div>
              )}
            </section>

            <section className="mt-8 border-t border-slate-200 pt-6">
              <div className="grid gap-4 lg:grid-cols-5">
                <div className="lg:col-span-3">
                {topAccounts.data && topAccounts.data.length > 0 ? (
                  <BarChartCost data={topAccounts.data} currency={filters.currency} />
                ) : (
                  <Card>
                    <CardContent className="p-6 text-sm text-slate-500">Sem dados para análise de barras no período.</CardContent>
                  </Card>
                )}
              </div>
              <div className="lg:col-span-2">
                {topAccounts.data && topAccounts.data.length > 0 ? (
                  <LinkedAccountTable data={topAccounts.data} currency={filters.currency} />
                ) : (
                  <Card>
                    <CardContent className="p-6 text-sm text-slate-500">Sem dados de linked accounts.</CardContent>
                  </Card>
                )}
              </div>
              </div>
            </section>

            <section className="mt-8 border-t border-slate-200 pt-6">
              <div className="grid gap-4 lg:grid-cols-5">
                <div className="lg:col-span-3">
                {daily.data && daily.data.length > 0 ? (
                  <LineChartDaily data={daily.data} currency={filters.currency} />
                ) : (
                  <Card>
                    <CardContent className="p-6 text-sm text-slate-500">Sem dados de evolução diária.</CardContent>
                  </Card>
                )}
                </div>
                <div className="lg:col-span-2">
                {topServices.data && topServices.data.length > 0 ? (
                  <TopServicesTable data={topServices.data} currency={filters.currency} />
                ) : (
                  <Card>
                    <CardContent className="p-6 text-sm text-slate-500">Sem dados de serviços.</CardContent>
                  </Card>
                )}
                </div>
              </div>
            </section>

            <section className="mt-8 grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 md:grid-cols-3">
              <div className="flex items-center gap-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
                <BarChart3 className="h-4 w-4" />
                ANÁLISE CONSOLIDADA
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
                <CalendarRange className="h-4 w-4" />
                VISÃO SEMANAL
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
                <Wallet className="h-4 w-4" />
                ORÇAMENTO E EXECUÇÃO
              </div>
            </section>

            {summary.data && daily.data && topServices.data && topAccounts.data ? (
              <WeeklyDrilldownModal
                open={drilldownOpen}
                onOpenChange={setDrilldownOpen}
                filters={filters}
                summary={summary.data}
                daily={daily.data}
                topServices={topServices.data}
                topAccounts={topAccounts.data}
                currency={filters.currency}
              />
            ) : null}
          </>
        ) : null}
      </main>
    </div>
  );
}
