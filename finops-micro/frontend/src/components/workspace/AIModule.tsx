"use client";

import { AiAssistant } from "@/components/ai/AiAssistant";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { useAppContext } from "@/contexts/AppContext";

export function AIModule() {
  const { filters } = useAppContext();

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumbs items={[{ label: filters.cloud.toUpperCase() }, { label: "AI Insights" }]} />
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">AI insights</h1>
        <p className="mt-1 text-sm text-slate-500">Interface contextual para análise assistida dos dados de custo.</p>
      </div>
      <AiAssistant filters={filters} />
    </div>
  );
}
