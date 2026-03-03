"use client";

import Link from "next/link";
import { ArrowLeft, CalendarRange, FileOutput, Layers3, LineChart, Wallet } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/dashboard/EmptyState";
import { LoadingGrid } from "@/components/dashboard/LoadingGrid";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { BarChartCost } from "@/components/charts/BarChartCost";
import { LineChartDaily } from "@/components/charts/LineChartDaily";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { LinkedAccountTable } from "@/components/tables/LinkedAccountTable";
import { TopServicesTable } from "@/components/tables/TopServicesTable";
import { Button } from "@/components/ui/button";
import { useAppContext } from "@/contexts/AppContext";
import { useDailyQuery, useSummaryQuery, useTopAccountsQuery, useTopServicesQuery } from "@/hooks/use-finops-queries";
import { formatCompactMoney, formatMoney, formatNumber, formatPct } from "@/lib/format";
import { toSearchParams } from "@/lib/query/search-params";
import { openWeeklyDetailReport } from "@/lib/reports/weekly-detail-report";

export function WeeklyDetailModule() {
  const { filters } = useAppContext();
  const [isExportingPdf, setIsExportingPdf] = useState(false);

  const summary = useSummaryQuery(filters);
  const daily = useDailyQuery(filters);
  const topServices = useTopServicesQuery(filters);
  const topAccounts = useTopAccountsQuery(filters);

  const isLoading = summary.isLoading || daily.isLoading || topServices.isLoading || topAccounts.isLoading;
  const hasData = Boolean(summary.data && daily.data && topServices.data && topAccounts.data);
  const overviewHref = `/overview?${toSearchParams(filters).toString()}`;

  function handleExportPdf() {
    if (!summary.data || !daily.data || !topServices.data || !topAccounts.data) {
      return;
    }

    setIsExportingPdf(true);
    openWeeklyDetailReport({
      cloud: filters.cloud,
      from: filters.from,
      to: filters.to,
      currency: filters.currency,
      summary: summary.data,
      daily: daily.data,
      topServices: topServices.data,
      topAccounts: topAccounts.data,
    });
    window.setTimeout(() => setIsExportingPdf(false), 300);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-3">
          <Breadcrumbs
            items={[
              { label: filters.cloud.toUpperCase() },
              { label: "Overview", href: overviewHref },
              { label: "Weekly Detail" },
            ]}
          />
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Visão detalhada semanal</h1>
            <p className="mt-1 text-sm text-slate-500">
              Quebra operacional do período com KPIs, tendência diária, serviços e contas mais relevantes.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="button"
            variant="default"
            onClick={handleExportPdf}
            disabled={!hasData || isLoading || isExportingPdf}
            className="bg-emerald-700 px-4 py-2 text-sm font-semibold hover:bg-emerald-800"
          >
            <FileOutput className="mr-2 h-4 w-4" />
            {isExportingPdf ? "Gerando PDF..." : "Emitir PDF"}
          </Button>

          <Link
            href={overviewHref}
            className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 transition-colors hover:bg-slate-50"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar ao overview
          </Link>
        </div>
      </div>

      {isLoading ? <LoadingGrid cards={6} /> : null}

      {!isLoading && !hasData ? (
        <EmptyState
          title="Sem dados para a visão detalhada"
          description="Ajuste o período ou execute um refresh para consolidar o detalhamento semanal."
        />
      ) : null}

      {!isLoading && hasData && summary.data ? (
        <>
          <section className="grid gap-4 xl:grid-cols-12">
            <div className="rounded-3xl border border-emerald-900/10 bg-[radial-gradient(circle_at_top,#166534,#064E3B)] p-6 text-white shadow-soft xl:col-span-5">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-emerald-100">Consumo semanal</p>
              <h2 className="mt-4 text-4xl font-semibold tracking-tight">
                {formatCompactMoney(summary.data.totalWeek, filters.currency)}
              </h2>
              <p className="mt-2 text-sm text-emerald-100">
                Delta do período: {formatPct(summary.data.deltaWeek)}
              </p>
              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <DetailMetric
                  icon={<CalendarRange className="h-4 w-4" />}
                  label="Período"
                  value={`${filters.from} - ${filters.to}`}
                />
                <DetailMetric
                  icon={<Wallet className="h-4 w-4" />}
                  label="Média diária"
                  value={formatMoney(summary.data.avgDaily, filters.currency)}
                />
                <DetailMetric
                  icon={<LineChart className="h-4 w-4" />}
                  label="Maior dia"
                  value={formatMoney(summary.data.peakDay.amount, filters.currency)}
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:col-span-7 xl:grid-cols-4">
              <MiniMetric label="Budget mensal" value={formatCompactMoney(summary.data.budgetMonth ?? 0, filters.currency)} />
              <MiniMetric label="Total do mês" value={formatCompactMoney(summary.data.monthTotal, filters.currency)} />
              <MiniMetric label="Total do ano" value={formatCompactMoney(summary.data.yearTotal, filters.currency)} />
              <MiniMetric label="Cotação USD" value={formatNumber(summary.data.usdRate ?? 0)} />
            </div>
          </section>

          <section className="grid gap-4 xl:grid-cols-5">
            <div className="xl:col-span-3">
              <SectionCard
                title="Evolução diária"
                description="Curva diária do período selecionado com foco nas principais linhas de custo."
                contentClassName="p-2 pt-0"
              >
                <LineChartDaily data={daily.data ?? []} currency={filters.currency} title="Evolução diária" />
              </SectionCard>
            </div>
            <div className="xl:col-span-2">
              <SectionCard
                title="Entidades por custo"
                description="Distribuição por linked account no mesmo recorte."
                contentClassName="p-2 pt-0"
              >
                <BarChartCost data={topAccounts.data ?? []} currency={filters.currency} chartType="bar" />
              </SectionCard>
            </div>
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-xl bg-emerald-50 p-2 text-emerald-700">
                  <Layers3 className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">Top serviços</p>
                  <p className="text-xs text-slate-500">Ranking dos serviços mais relevantes no período.</p>
                </div>
              </div>
              <TopServicesTable data={topServices.data ?? []} currency={filters.currency} title="Top serviços" />
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-xl bg-emerald-50 p-2 text-emerald-700">
                  <Wallet className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">Top entidades</p>
                  <p className="text-xs text-slate-500">Contas com maior participação no período selecionado.</p>
                </div>
              </div>
              <LinkedAccountTable data={topAccounts.data ?? []} currency={filters.currency} title="Top entidades" />
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

function DetailMetric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/10 p-3 backdrop-blur">
      <div className="flex items-center gap-2 text-emerald-100">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
    </div>
  );
}
