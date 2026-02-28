"use client";

import { KPIStatCard } from "@/components/dashboard/KPIStatCard";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { useAppContext } from "@/contexts/AppContext";
import { useSummaryQuery } from "@/hooks/use-finops-queries";

export function BudgetsModule() {
  const { filters } = useAppContext();
  const summary = useSummaryQuery(filters);

  const monthGap = summary.data ? (summary.data.budgetMonth ?? 0) - summary.data.monthTotal : null;
  const yearGap = summary.data ? (summary.data.budgetYear ?? 0) - summary.data.yearTotal : null;

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumbs items={[{ label: filters.cloud.toUpperCase() }, { label: "Budgets" }]} />
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Budget performance</h1>
        <p className="mt-1 text-sm text-slate-500">Acompanhamento de meta versus execução com leitura executiva.</p>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KPIStatCard title="Meta mensal" value={summary.data?.budgetMonth} currency={filters.currency} valueType="compact-money" />
        <KPIStatCard title="Executado no mês" value={summary.data?.monthTotal} currency={filters.currency} valueType="compact-money" />
        <KPIStatCard title="Saldo mensal" value={monthGap} currency={filters.currency} valueType="compact-money" />
        <KPIStatCard title="Saldo anual" value={yearGap} currency={filters.currency} valueType="compact-money" />
      </section>

      <SectionCard title="Budget notes" description="Área preparada para futuras integrações de forecast e alertas.">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Meta mensal</p>
            <p className="mt-2 text-sm text-slate-500">Usa o contrato atual do backend (`budgetMonth`) sem alterar regras de negócio.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Meta anual</p>
            <p className="mt-2 text-sm text-slate-500">Consolidação contínua com `budgetYear` e `yearTotal`.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Forecast</p>
            <p className="mt-2 text-sm text-slate-500">Placeholder visual pronto para evolução futura sem quebrar o layout enterprise.</p>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
