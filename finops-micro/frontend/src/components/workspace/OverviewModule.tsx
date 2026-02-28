"use client";

import { BarChart3, CalendarRange, Wallet } from "lucide-react";
import { useState } from "react";

import { HealthIndicator } from "@/components/dashboard/HealthIndicator";
import { KPIStatCard } from "@/components/dashboard/KPIStatCard";
import { LoadingGrid } from "@/components/dashboard/LoadingGrid";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { BarChartCost } from "@/components/charts/BarChartCost";
import { LineChartDaily } from "@/components/charts/LineChartDaily";
import { WeeklyDrilldownModal } from "@/components/drilldown/WeeklyDrilldownModal";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { LinkedAccountTable } from "@/components/tables/LinkedAccountTable";
import { TopServicesTable } from "@/components/tables/TopServicesTable";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAppContext } from "@/contexts/AppContext";
import { useDailyQuery, useSummaryQuery, useTopAccountsQuery, useTopServicesQuery } from "@/hooks/use-finops-queries";

export function OverviewModule() {
  const { filters } = useAppContext();
  const [drilldownOpen, setDrilldownOpen] = useState(false);
  const [accountsChartType, setAccountsChartType] = useState<"bar" | "line" | "pie">("bar");
  const [dailyChartType, setDailyChartType] = useState<"line" | "bar" | "pie">("line");

  const chartFilters = { ...filters, topN: filters.topN };
  const summary = useSummaryQuery(filters);
  const daily = useDailyQuery(chartFilters);
  const topServices = useTopServicesQuery(chartFilters);
  const topAccounts = useTopAccountsQuery(chartFilters);

  const isLoading = summary.isLoading || daily.isLoading || topServices.isLoading || topAccounts.isLoading;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-3">
          <Breadcrumbs
            items={[
              { label: filters.cloud.toUpperCase() },
              { label: "Overview" },
            ]}
          />
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Overview executivo</h1>
            <p className="mt-1 text-sm text-slate-500">
              Visão consolidada de custos, desempenho e execução orçamentária para o período selecionado.
            </p>
          </div>
        </div>
        <HealthIndicator loading={isLoading} hasData={Boolean(summary.data)} cloud={filters.cloud} />
      </div>

      {isLoading || !summary.data ? (
        <LoadingGrid cards={5} />
      ) : (
        <section className="grid gap-4 xl:grid-cols-12">
          <div className="xl:col-span-4">
            <KPIStatCard
              title="Consumo do período"
              value={summary.data.totalWeek}
              currency={filters.currency}
              delta={summary.data.deltaWeek}
              tone="hero"
              valueType="compact-money"
              subtitle="Comparado ao período anterior equivalente"
              onClick={() => setDrilldownOpen(true)}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 xl:col-span-8 xl:grid-cols-4">
            <KPIStatCard title="Meta mensal" value={summary.data.budgetMonth} currency={filters.currency} valueType="compact-money" />
            <KPIStatCard title="Total do mês" value={summary.data.monthTotal} currency={filters.currency} valueType="compact-money" />
            <KPIStatCard title="Total do ano" value={summary.data.yearTotal} currency={filters.currency} valueType="compact-money" />
            <KPIStatCard title="Cotação USD" value={summary.data.usdRate} currency={filters.currency} valueType="number" />
          </div>
        </section>
      )}

      <section className="grid gap-4 xl:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-50 p-2 text-emerald-700">
              <BarChart3 className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">Análise consolidada</p>
              <p className="text-xs text-slate-500">Custos por conta e serviço com visão executiva.</p>
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-50 p-2 text-emerald-700">
              <CalendarRange className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">Tendência temporal</p>
              <p className="text-xs text-slate-500">Monitoramento diário de variação e picos.</p>
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-50 p-2 text-emerald-700">
              <Wallet className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">Budget posture</p>
              <p className="text-xs text-slate-500">Meta contra execução com leitura rápida.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-5">
        <div className="xl:col-span-3">
          <SectionCard
            title="Análise de dados"
            description="Breakdown por linked account para investigação rápida."
            action={
              <div className="w-[160px]">
                <Select value={accountsChartType} onValueChange={(value) => setAccountsChartType(value as "bar" | "line" | "pie")}>
                  <SelectTrigger className="h-9 bg-white">
                    <SelectValue placeholder="Visualização" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="bar">Barras</SelectItem>
                    <SelectItem value="line">Linha</SelectItem>
                    <SelectItem value="pie">Pizza</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            }
            contentClassName="p-2 pt-0"
          >
            <BarChartCost data={topAccounts.data ?? []} currency={filters.currency} chartType={accountsChartType} />
          </SectionCard>
        </div>
        <div className="xl:col-span-2">
          <LinkedAccountTable data={topAccounts.data ?? []} currency={filters.currency} title="Linked Accounts" />
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-5">
        <div className="xl:col-span-3">
          <SectionCard
            title="Trends"
            description="Evolução diária dos custos no recorte atual."
            action={
              <div className="w-[160px]">
                <Select value={dailyChartType} onValueChange={(value) => setDailyChartType(value as "line" | "bar" | "pie")}>
                  <SelectTrigger className="h-9 bg-white">
                    <SelectValue placeholder="Visualização" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="line">Linha</SelectItem>
                    <SelectItem value="bar">Barras</SelectItem>
                    <SelectItem value="pie">Pizza</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            }
            contentClassName="p-2 pt-0"
          >
            <LineChartDaily data={daily.data ?? []} currency={filters.currency} chartType={dailyChartType} title="Evolução diária" />
          </SectionCard>
        </div>
        <div className="xl:col-span-2">
          <TopServicesTable data={topServices.data ?? []} currency={filters.currency} title="Top serviços" />
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
    </div>
  );
}
