"use client";

import Link from "next/link";

import { LineChartDaily } from "@/components/charts/LineChartDaily";
import { KpiCard } from "@/components/kpi/KpiCard";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { LinkedAccountTable } from "@/components/tables/LinkedAccountTable";
import { TopServicesTable } from "@/components/tables/TopServicesTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

export default function WeeklyPage() {
  const { filters, updateFilters } = useDashboardFilters();
  const chartFilters = { ...filters, topN: 10 };

  const month = filters.from.slice(0, 7);
  const summary = useSummaryQuery(filters);
  const daily = useDailyQuery(chartFilters);
  const topServices = useTopServicesQuery(chartFilters);
  const topAccounts = useTopAccountsQuery(chartFilters);
  const filterOptions = useFilterOptionsQuery(filters.cloud, month);

  const query = toSearchParams(filters).toString();

  return (
    <div className="flex min-h-screen bg-app-bg">
      <Sidebar
        filters={filters}
        services={filterOptions.data?.services ?? []}
        accounts={filterOptions.data?.accounts ?? []}
        onFiltersChange={updateFilters}
      />

      <main className="w-full p-4 md:ml-[300px] md:p-8">
        <Header cloud={filters.cloud} activeTab="dashboard" filtersQuery={query} />

        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold">VISÃO DETALHADA — CONSUMO SEMANAL ({filters.cloud.toUpperCase()})</h2>
          <Link href={`/dashboard?${query}`}>
            <Button variant="outline">Voltar ao dashboard</Button>
          </Link>
        </div>

        {summary.isLoading || !summary.data ? (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-[130px]" />
            ))}
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard title="TOTAL SEMANAL" value={summary.data.totalWeek} currency={filters.currency} delta={summary.data.deltaWeek} />
            <KpiCard title="MÉDIA DIÁRIA" value={summary.data.avgDaily} currency={filters.currency} />
            <KpiCard title="MAIOR DIA" value={summary.data.peakDay.amount} currency={filters.currency} />
            <KpiCard title="TOTAL MÊS" value={summary.data.monthTotal} currency={filters.currency} />
          </div>
        )}

        <section className="mt-6">
          {daily.data?.length ? (
            <LineChartDaily data={daily.data} currency={filters.currency} title="EVOLUÇÃO DIÁRIA SEMANAL" />
          ) : (
            <Card>
              <CardContent className="p-6 text-sm text-slate-500">Sem dados para evolução diária no período.</CardContent>
            </Card>
          )}
        </section>

        <section className="mt-6 grid gap-4 lg:grid-cols-2">
          {topServices.data?.length ? (
            <TopServicesTable data={topServices.data} currency={filters.currency} title="PRINCIPAIS QUEBRAS - SERVIÇOS" />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>PRINCIPAIS QUEBRAS - SERVIÇOS</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-slate-500">Sem dados.</CardContent>
            </Card>
          )}
          {topAccounts.data?.length ? (
            <LinkedAccountTable data={topAccounts.data} currency={filters.currency} title="PRINCIPAIS QUEBRAS - ENTIDADES" />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>PRINCIPAIS QUEBRAS - ENTIDADES</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-slate-500">Sem dados.</CardContent>
            </Card>
          )}
        </section>
      </main>
    </div>
  );
}
