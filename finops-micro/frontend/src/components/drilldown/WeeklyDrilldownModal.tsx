"use client";

import Link from "next/link";

import { LineChartDaily } from "@/components/charts/LineChartDaily";
import { KpiCard } from "@/components/kpi/KpiCard";
import { LinkedAccountTable } from "@/components/tables/LinkedAccountTable";
import { TopServicesTable } from "@/components/tables/TopServicesTable";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { Currency } from "@/lib/format";
import type { DashboardFilters } from "@/lib/query/search-params";
import type { DailyResponse, SummaryResponse, TopAccountsResponse, TopServicesResponse } from "@/lib/schemas/finops";

type WeeklyDrilldownModalProps = {
  open: boolean;
  onOpenChange: (value: boolean) => void;
  filters: DashboardFilters;
  summary: SummaryResponse;
  daily: DailyResponse;
  topServices: TopServicesResponse;
  topAccounts: TopAccountsResponse;
  currency: Currency;
};

export function WeeklyDrilldownModal({
  open,
  onOpenChange,
  summary,
  daily,
  topServices,
  topAccounts,
  currency,
  filters,
}: WeeklyDrilldownModalProps) {
  const params = new URLSearchParams({
    cloud: filters.cloud,
    from: filters.from,
    to: filters.to,
    currency: filters.currency,
    topN: String(filters.topN),
    services: filters.services.join(","),
    accounts: filters.accounts.join(","),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>CONSUMO SEMANAL ({filters.cloud.toUpperCase()})</DialogTitle>
          <DialogDescription>KPIs, evolução diária e principais quebras</DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 md:grid-cols-4">
          <KpiCard title="Total da semana" value={summary.totalWeek} currency={currency} delta={summary.deltaWeek} />
          <KpiCard title="Média diária" value={summary.avgDaily} currency={currency} />
          <KpiCard title="Maior dia" value={summary.peakDay.amount} currency={currency} />
          <KpiCard title="Total mês" value={summary.monthTotal} currency={currency} />
        </div>

        <div className="mt-4">
          <LineChartDaily data={daily} currency={currency} title="EVOLUÇÃO DIÁRIA" />
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <TopServicesTable data={topServices} currency={currency} title="TOP SERVIÇOS" />
          <LinkedAccountTable data={topAccounts} currency={currency} title="TOP ENTIDADES" />
        </div>

        <div className="mt-4 flex justify-end">
          <Link href={`/dashboard/weekly?${params.toString()}`}>
            <Button>Abrir visão detalhada</Button>
          </Link>
        </div>
      </DialogContent>
    </Dialog>
  );
}
