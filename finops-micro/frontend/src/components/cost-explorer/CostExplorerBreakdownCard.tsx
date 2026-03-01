"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { EmptyState } from "@/components/dashboard/EmptyState";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { cn } from "@/lib/utils";
import { formatCompactMoney, formatPct, type Currency } from "@/lib/format";
import type { CostExplorerBreakdownResponse } from "@/lib/schemas/finops";

type GroupBy = "service" | "account";

type CostExplorerBreakdownCardProps = {
  data?: CostExplorerBreakdownResponse;
  isLoading: boolean;
  currency: Currency;
  groupBy: GroupBy;
  selectedItem: string | null;
  onGroupByChange: (groupBy: GroupBy) => void;
  onSelectItem: (item: string) => void;
};

export function CostExplorerBreakdownCard({
  data,
  isLoading,
  currency,
  groupBy,
  selectedItem,
  onGroupByChange,
  onSelectItem,
}: CostExplorerBreakdownCardProps) {
  const title = groupBy === "service" ? "Services breakdown" : "Accounts breakdown";
  const description = groupBy === "service" ? "Concentracao e variacao por servico." : "Concentracao e variacao por conta.";

  return (
    <SectionCard
      title={title}
      description={description}
      hint={`Mostra como o custo está distribuído por ${groupBy === "service" ? "serviço" : "conta"}, com participação no total, variação versus o período anterior e contribuição para o movimento do custo.`}
      action={
        <div className="inline-flex rounded-2xl border border-slate-200 bg-slate-50 p-1">
          {(["service", "account"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => onGroupByChange(value)}
              className={cn(
                "rounded-xl px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] transition",
                groupBy === value ? "bg-emerald-600 text-white shadow-sm" : "text-slate-500 hover:text-slate-700",
              )}
            >
              {value}
            </button>
          ))}
        </div>
      }
    >
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="h-16 animate-pulse rounded-2xl bg-slate-100" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState title="Sem breakdown" description="Nao ha itens suficientes para compor o breakdown deste recorte." />
      ) : (
        <div className="space-y-3">
          {data.map((item, index) => {
            const positive = item.delta >= 0;
            const isActive = item.label === selectedItem;
            return (
              <button
                key={`${item.key}-${index}`}
                type="button"
                onClick={() => onSelectItem(item.label)}
                className={cn(
                  "w-full rounded-2xl border px-4 py-4 text-left transition",
                  isActive ? "border-emerald-200 bg-emerald-50" : "border-slate-200 bg-slate-50 hover:border-slate-300",
                )}
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex items-center gap-3">
                      <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white text-xs font-semibold text-slate-500 shadow-sm">
                        {index + 1}
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-slate-900">{item.label}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                          Share {item.sharePct.toFixed(1)}% · Contribution {item.contributionPct.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 h-2 rounded-full bg-white">
                      <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${Math.max(item.sharePct, 2)}%` }} />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3 lg:min-w-[320px]">
                    <MetricBox label="Total" value={formatCompactMoney(item.total, currency)} />
                    <MetricBox label="Delta" value={formatCompactMoney(item.delta, currency)} tone={positive ? "positive" : "negative"} />
                    <MetricBox
                      label="Delta %"
                      value={formatPct(item.deltaPct)}
                      icon={positive ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
                      tone={positive ? "positive" : "negative"}
                    />
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </SectionCard>
  );
}

function MetricBox({
  label,
  value,
  icon,
  tone = "default",
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
  tone?: "default" | "positive" | "negative";
}) {
  const toneClass =
    tone === "positive" ? "text-emerald-700" : tone === "negative" ? "text-rose-700" : "text-slate-900";

  return (
    <div className="rounded-2xl bg-white p-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <div className={cn("mt-2 flex items-center gap-1 text-sm font-semibold", toneClass)}>
        {icon}
        <span>{value}</span>
      </div>
    </div>
  );
}
