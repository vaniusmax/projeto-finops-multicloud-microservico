"use client";

import { EmptyState } from "@/components/dashboard/EmptyState";
import { SectionCard } from "@/components/dashboard/SectionCard";
import { formatMoney, formatPct, type Currency } from "@/lib/format";
import type { CostExplorerBreakdownResponse } from "@/lib/schemas/finops";

type CostExplorerVarianceTableProps = {
  data?: CostExplorerBreakdownResponse;
  isLoading: boolean;
  currency: Currency;
};

export function CostExplorerVarianceTable({ data, isLoading, currency }: CostExplorerVarianceTableProps) {
  return (
    <SectionCard
      title="Variance table"
      description="Impacto absoluto, percentual e contribuicao para o crescimento."
      hint="Tabela detalhada para comparar os itens do breakdown. Mostra total, participação no custo, delta versus o período anterior e quanto cada item explica do movimento do custo."
    >
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 7 }).map((_, index) => (
            <div key={index} className="h-12 animate-pulse rounded-2xl bg-slate-100" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState title="Sem variacao para exibir" description="Nao ha itens suficientes para preencher a tabela deste recorte." />
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr className="text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                <th className="pb-3 pr-4">Item</th>
                <th className="pb-3 pr-4">Total</th>
                <th className="pb-3 pr-4">Share</th>
                <th className="pb-3 pr-4">Delta</th>
                <th className="pb-3 pr-4">Delta %</th>
                <th className="pb-3">Contribution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((item) => (
                <tr key={item.key} className="align-top">
                  <td className="py-4 pr-4 font-medium text-slate-900">{item.label}</td>
                  <td className="py-4 pr-4 text-slate-600">{formatMoney(item.total, currency)}</td>
                  <td className="py-4 pr-4 text-slate-600">{item.sharePct.toFixed(1)}%</td>
                  <td className={`py-4 pr-4 ${item.delta >= 0 ? "text-emerald-700" : "text-rose-700"}`}>{formatMoney(item.delta, currency)}</td>
                  <td className={`py-4 pr-4 ${item.delta >= 0 ? "text-emerald-700" : "text-rose-700"}`}>{formatPct(item.deltaPct)}</td>
                  <td className="py-4 text-slate-600">{item.contributionPct.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionCard>
  );
}
