"use client";

import { useMemo, useState } from "react";

import { AnalyticsInsightPanel } from "@/components/analytics/AnalyticsInsightPanel";
import { EmptyState } from "@/components/dashboard/EmptyState";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { BarChartCost } from "@/components/charts/BarChartCost";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { LinkedAccountTable } from "@/components/tables/LinkedAccountTable";
import { TopServicesTable } from "@/components/tables/TopServicesTable";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAppContext } from "@/contexts/AppContext";
import { useAnalyticsInsightsQuery, useSummaryQuery, useTopAccountsQuery, useTopServicesQuery } from "@/hooks/use-finops-queries";
import { formatMoney, formatPct } from "@/lib/format";
import type { DashboardFilters } from "@/lib/query/search-params";

const DAY_MS = 24 * 60 * 60 * 1000;
const periodFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "UTC",
});

function parseIsoDay(value: string): Date {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function toIsoDay(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function shiftDay(value: Date, days: number): Date {
  return new Date(value.getTime() + days * DAY_MS);
}

function weekRanges(referenceTo: string): {
  current: Pick<DashboardFilters, "from" | "to">;
  previous: Pick<DashboardFilters, "from" | "to">;
} {
  const referenceDate = parseIsoDay(referenceTo);
  const daysSinceSunday = referenceDate.getUTCDay();
  const currentWeekEnd = shiftDay(referenceDate, -daysSinceSunday);
  const currentWeekStart = shiftDay(currentWeekEnd, -6);
  const previousWeekEnd = shiftDay(currentWeekStart, -1);
  const previousWeekStart = shiftDay(previousWeekEnd, -6);
  return {
    current: {
      from: toIsoDay(currentWeekStart),
      to: toIsoDay(currentWeekEnd),
    },
    previous: {
      from: toIsoDay(previousWeekStart),
      to: toIsoDay(previousWeekEnd),
    },
  };
}

function formatPeriod(from: string, to: string): string {
  const fromLabel = periodFormatter.format(parseIsoDay(from));
  const toLabel = periodFormatter.format(parseIsoDay(to));
  return `${fromLabel} a ${toLabel}`;
}

export function AnalyticsModule() {
  const { filters } = useAppContext();
  const [chartType, setChartType] = useState<"bar" | "line" | "pie">("bar");
  const comparisonWeeks = useMemo(
    () => weekRanges(filters.to),
    [filters.to],
  );
  const currentWeekFilters = useMemo(
    () => ({ ...filters, ...comparisonWeeks.current }),
    [comparisonWeeks, filters],
  );
  const previousWeekFilters = useMemo(
    () => ({ ...filters, ...comparisonWeeks.previous }),
    [comparisonWeeks, filters],
  );
  const summary = useSummaryQuery(currentWeekFilters);
  const previousSummary = useSummaryQuery(previousWeekFilters);
  const topAccounts = useTopAccountsQuery(filters);
  const topServices = useTopServicesQuery(filters);
  const insights = useAnalyticsInsightsQuery(filters);

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumbs items={[{ label: filters.cloud.toUpperCase() }, { label: "Analytics" }]} />
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Analytics workspace</h1>
        <p className="mt-1 text-sm text-slate-500">Investigação de contas e serviços com foco operacional.</p>
      </div>

      <SectionCard
        title="Comparativo explícito de período"
        description="Exibe semanas fechadas de segunda a domingo: semana atual e semana imediatamente anterior."
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Semana atual (seg-dom)</p>
            <p className="mt-2 text-sm font-medium text-slate-700">
              {formatPeriod(comparisonWeeks.current.from, comparisonWeeks.current.to)}
            </p>
            <p className="mt-3 text-2xl font-semibold text-slate-900">
              {summary.data ? formatMoney(summary.data.totalWeek, filters.currency) : "—"}
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Semana anterior (seg-dom)</p>
            <p className="mt-2 text-sm font-medium text-slate-700">
              {formatPeriod(comparisonWeeks.previous.from, comparisonWeeks.previous.to)}
            </p>
            <p className="mt-3 text-2xl font-semibold text-slate-900">
              {previousSummary.data ? formatMoney(previousSummary.data.totalWeek, filters.currency) : "—"}
            </p>
          </div>
        </div>
        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
          {summary.data ? (
            <span>
              Variação vs período anterior:{" "}
              <strong className={summary.data.deltaWeek >= 0 ? "text-emerald-700" : "text-rose-700"}>
                {formatPct(summary.data.deltaWeek)}
              </strong>
            </span>
          ) : (
            "Calculando variação..."
          )}
        </div>
      </SectionCard>

      <AnalyticsInsightPanel data={insights.data} isLoading={insights.isLoading} />

      <section className="grid gap-4 xl:grid-cols-5">
        <div className="xl:col-span-3">
          <SectionCard
            title="Linked account breakdown"
            description="Ranking e participação percentual das contas."
            action={
              <div className="w-[160px]">
                <Select value={chartType} onValueChange={(value) => setChartType(value as "bar" | "line" | "pie")}>
                  <SelectTrigger className="h-9 bg-white">
                    <SelectValue />
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
            {topAccounts.data?.length ? (
              <BarChartCost data={topAccounts.data} currency={filters.currency} chartType={chartType} />
            ) : (
              <EmptyState title="Sem dados de contas" description="Ajuste filtros avançados ou amplie o período analisado." />
            )}
          </SectionCard>
        </div>
        <div className="xl:col-span-2">
          <LinkedAccountTable data={topAccounts.data ?? []} currency={filters.currency} title="Grid de contas" />
        </div>
      </section>

      <TopServicesTable data={topServices.data ?? []} currency={filters.currency} title="Services leaderboard" />
    </div>
  );
}
