"use client";

import { useState } from "react";

import { EmptyState } from "@/components/dashboard/EmptyState";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { BarChartCost } from "@/components/charts/BarChartCost";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { LinkedAccountTable } from "@/components/tables/LinkedAccountTable";
import { TopServicesTable } from "@/components/tables/TopServicesTable";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAppContext } from "@/contexts/AppContext";
import { useTopAccountsQuery, useTopServicesQuery } from "@/hooks/use-finops-queries";

export function AnalyticsModule() {
  const { filters } = useAppContext();
  const [chartType, setChartType] = useState<"bar" | "line" | "pie">("bar");
  const topAccounts = useTopAccountsQuery(filters);
  const topServices = useTopServicesQuery(filters);

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumbs items={[{ label: filters.cloud.toUpperCase() }, { label: "Analytics" }]} />
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Analytics workspace</h1>
        <p className="mt-1 text-sm text-slate-500">Investigação de contas e serviços com foco operacional.</p>
      </div>

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
