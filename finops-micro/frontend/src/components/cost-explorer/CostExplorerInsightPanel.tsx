"use client";

import { AlertTriangle, BrainCircuit, ChevronRight, Sparkles, Target } from "lucide-react";

import { EmptyState } from "@/components/dashboard/EmptyState";
import { SectionCard } from "@/components/dashboard/SectionCard";
import type { CostExplorerInsightResponse } from "@/lib/schemas/finops";

type CostExplorerInsightPanelProps = {
  data?: CostExplorerInsightResponse;
  isLoading: boolean;
  onSelectDrilldown: (value: string) => void;
};

export function CostExplorerInsightPanel({ data, isLoading, onSelectDrilldown }: CostExplorerInsightPanelProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 xl:grid-cols-12">
        <div className="xl:col-span-5 h-[260px] animate-pulse rounded-3xl bg-slate-200" />
        <div className="xl:col-span-3 h-[260px] animate-pulse rounded-3xl bg-slate-200" />
        <div className="xl:col-span-4 h-[260px] animate-pulse rounded-3xl bg-slate-200" />
      </div>
    );
  }

  if (!data) {
    return <EmptyState title="Sem insights do Cost Explorer" description="Nao foi possivel montar a camada interpretativa deste recorte." />;
  }

  return (
    <section className="grid gap-4 xl:grid-cols-12">
      <div className="xl:col-span-5">
        <SectionCard
          title="Cost AI Summary"
          description={`Leitura complementar em modo ${data.mode === "llm" ? "LLM" : "heuristico"}.`}
          hint="Resumo interpretativo do recorte atual. Ele explica a distribuição do custo e sugere leitura analítica, mas não altera os números determinísticos da tela."
        >
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800">
              <BrainCircuit className="h-3.5 w-3.5" />
              {data.mode === "llm" ? "Copilot ativo" : "Fallback deterministico"}
            </div>
            <p className="text-sm leading-6 text-slate-600">{data.summary}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <MetricBadge label="Total" value={data.evidence.totalPeriod.toFixed(2)} />
              <MetricBadge label="Delta" value={`${data.evidence.deltaPeriodPct.toFixed(2)}%`} />
              <MetricBadge label="Group by" value={data.evidence.groupBy} />
              <MetricBadge label="Focus" value={data.evidence.selectedItem ?? "Auto"} />
            </div>
          </div>
        </SectionCard>
      </div>

      <div className="xl:col-span-3">
        <ListCard
          title="Drivers"
          items={data.drivers}
          tone="emerald"
          icon={<Sparkles className="h-4 w-4" />}
          hint="Principais fatores que explicam o comportamento do custo no período, como concentração, crescimento ou redução."
        />
      </div>

      <div className="xl:col-span-4">
        <ListCard
          title="Watchouts"
          items={data.risks}
          tone="amber"
          icon={<AlertTriangle className="h-4 w-4" />}
          hint="Pontos de atenção encontrados no recorte atual. Normalmente destacam risco de concentração, picos de consumo ou comportamento atípico."
        />
      </div>

      <div className="xl:col-span-7">
        <SectionCard
          title="Recommended Actions"
          description="Acoes priorizadas para o proximo passo de investigacao."
          hint="Lista das próximas ações sugeridas para investigar ou otimizar o custo. Ajuda a transformar a análise em plano de execução."
        >
          <div className="grid gap-3">
            {data.actions.map((action, index) => (
              <div key={`${action.title}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-900">{action.title}</p>
                  <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600">{action.priority}</span>
                </div>
                <p className="mt-2 text-sm text-slate-500">{action.rationale}</p>
                <p className="mt-3 text-xs font-medium uppercase tracking-wide text-slate-400">{action.owner}</p>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>

      <div className="xl:col-span-5 space-y-4">
        <SectionCard
          title="Suggested Questions"
          description="Prompts uteis para a proxima iteracao analitica."
          hint="Perguntas que ajudam o usuário a aprofundar a investigação do custo, orientando a próxima leitura da tela."
        >
          <div className="space-y-3">
            {data.suggestedQuestions.map((question, index) => (
              <div key={`${question}-${index}`} className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4">
                <div className="rounded-xl bg-emerald-50 p-2 text-emerald-700">
                  <Target className="h-4 w-4" />
                </div>
                <p className="text-sm text-slate-600">{question}</p>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="Suggested Drilldowns"
          description="Atalhos de navegacao recomendados para este recorte."
          hint="Sugestões de próximos cortes analíticos. Ao clicar, o foco da tela muda para o item mais promissor para aprofundar a análise."
        >
          <div className="space-y-3">
            {data.nextDrilldowns.map((item, index) => (
              <button
                key={`${item.value}-${index}`}
                type="button"
                onClick={() => onSelectDrilldown(item.value)}
                className="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:border-emerald-200 hover:bg-emerald-50"
              >
                <div>
                  <p className="text-sm font-semibold text-slate-900">{item.value}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-slate-400">{item.dimension}</p>
                  <p className="mt-2 text-sm text-slate-500">{item.reason}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-slate-400" />
              </button>
            ))}
          </div>
        </SectionCard>
      </div>
    </section>
  );
}

function MetricBadge({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className="mt-2 text-sm font-medium text-slate-900">{value}</p>
    </div>
  );
}

function ListCard({
  title,
  items,
  icon,
  tone,
  hint,
}: {
  title: string;
  items: string[];
  icon: React.ReactNode;
  tone: "emerald" | "amber";
  hint?: string;
}) {
  const toneClass =
    tone === "emerald"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : "border-amber-200 bg-amber-50 text-amber-800";

  return (
    <SectionCard title={title} description={`${title} inferidos a partir do payload do Cost Explorer.`} hint={hint}>
      <div className="space-y-3">
        <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${toneClass}`}>
          {icon}
          {title}
        </div>
        {items.length > 0 ? (
          items.map((item, index) => (
            <div key={`${title}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
              {item}
            </div>
          ))
        ) : (
          <p className="text-sm text-slate-500">Sem itens relevantes neste recorte.</p>
        )}
      </div>
    </SectionCard>
  );
}
