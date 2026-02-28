"use client";

import { useState } from "react";

import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { LineChartDaily } from "@/components/charts/LineChartDaily";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAppContext } from "@/contexts/AppContext";
import { useDailyQuery, useSummaryQuery } from "@/hooks/use-finops-queries";

export function TrendsModule() {
  const { filters, compareMode } = useAppContext();
  const [chartType, setChartType] = useState<"line" | "bar" | "pie">("line");
  const daily = useDailyQuery(filters);
  const summary = useSummaryQuery(filters);

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumbs items={[{ label: filters.cloud.toUpperCase() }, { label: "Trends" }]} />
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Trend analysis</h1>
        <p className="mt-1 text-sm text-slate-500">
          Monitoramento de evolução diária. Compare mode atual: {compareMode === "off" ? "desativado" : "período anterior equivalente"}.
        </p>
      </div>

      <section className="grid gap-4 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Delta semanal</p>
          <p className="mt-3 text-3xl font-semibold text-slate-900">{summary.data ? `${summary.data.deltaWeek.toFixed(2)}%` : "—"}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Média diária</p>
          <p className="mt-3 text-3xl font-semibold text-slate-900">{summary.data ? summary.data.avgDaily.toFixed(2) : "—"}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Maior dia</p>
          <p className="mt-3 text-3xl font-semibold text-slate-900">{summary.data?.peakDay.date ?? "—"}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Valor pico</p>
          <p className="mt-3 text-3xl font-semibold text-slate-900">{summary.data ? summary.data.peakDay.amount.toFixed(2) : "—"}</p>
        </div>
      </section>

      <SectionCard
        title="Daily evolution"
        description="Linha temporal do custo consolidado."
        action={
          <div className="w-[160px]">
            <Select value={chartType} onValueChange={(value) => setChartType(value as "line" | "bar" | "pie")}>
              <SelectTrigger className="h-9 bg-white">
                <SelectValue />
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
        <LineChartDaily data={daily.data ?? []} currency={filters.currency} chartType={chartType} title="Trend line" />
      </SectionCard>
    </div>
  );
}
