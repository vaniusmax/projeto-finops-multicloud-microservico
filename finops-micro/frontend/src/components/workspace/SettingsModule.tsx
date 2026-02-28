"use client";

import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { useAppContext } from "@/contexts/AppContext";

export function SettingsModule() {
  const { filters, compareMode, isSidebarCollapsed } = useAppContext();

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumbs items={[{ label: filters.cloud.toUpperCase() }, { label: "Settings" }]} />
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Workspace settings</h1>
        <p className="mt-1 text-sm text-slate-500">Preferências locais da experiência enterprise.</p>
      </div>

      <SectionCard title="Preferências da sessão" description="Persistidas em localStorage por enquanto.">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Cloud atual</p>
            <p className="mt-2 text-sm text-slate-500">{filters.cloud.toUpperCase()}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Compare mode</p>
            <p className="mt-2 text-sm text-slate-500">{compareMode}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Sidebar</p>
            <p className="mt-2 text-sm text-slate-500">{isSidebarCollapsed ? "Colapsada" : "Expandida"}</p>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
