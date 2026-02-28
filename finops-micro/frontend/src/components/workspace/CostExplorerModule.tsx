"use client";

import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { useAppContext } from "@/contexts/AppContext";
import { useTopAccountsQuery, useTopServicesQuery } from "@/hooks/use-finops-queries";

export function CostExplorerModule() {
  const { filters } = useAppContext();
  const topAccounts = useTopAccountsQuery(filters);
  const topServices = useTopServicesQuery(filters);

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumbs items={[{ label: filters.cloud.toUpperCase() }, { label: "Cost Explorer" }]} />
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Cost explorer</h1>
        <p className="mt-1 text-sm text-slate-500">Workspace modular para futuros groupings e drilldowns detalhados.</p>
      </div>

      <section className="grid gap-4 xl:grid-cols-2">
        <SectionCard title="Accounts snapshot" description="Top contas no recorte atual.">
          <div className="space-y-3">
            {(topAccounts.data ?? []).slice(0, 8).map((item) => (
              <div key={item.linkedAccount} className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                <span className="text-sm font-medium text-slate-800">{item.linkedAccount}</span>
                <span className="text-sm text-slate-500">{item.sharePct.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </SectionCard>
        <SectionCard title="Services snapshot" description="Top serviços no recorte atual.">
          <div className="space-y-3">
            {(topServices.data ?? []).slice(0, 8).map((item) => (
              <div key={item.serviceName} className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                <span className="text-sm font-medium text-slate-800">{item.serviceName}</span>
                <span className="text-sm text-slate-500">{item.sharePct.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
