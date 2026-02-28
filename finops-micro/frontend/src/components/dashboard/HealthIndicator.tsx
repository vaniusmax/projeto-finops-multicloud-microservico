"use client";

import { Activity, AlertTriangle, ShieldCheck } from "lucide-react";

type HealthIndicatorProps = {
  loading: boolean;
  hasData: boolean;
  cloud: string;
};

export function HealthIndicator({ loading, hasData, cloud }: HealthIndicatorProps) {
  if (loading) {
    return (
      <div className="inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
        <Activity className="h-3.5 w-3.5" />
        Atualizando dados de {cloud.toUpperCase()}
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-medium text-rose-700">
        <AlertTriangle className="h-3.5 w-3.5" />
        Sem dados consolidados
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
      <ShieldCheck className="h-3.5 w-3.5" />
      Pipeline saudável
    </div>
  );
}
