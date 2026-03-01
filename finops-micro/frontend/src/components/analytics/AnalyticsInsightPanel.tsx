"use client";

import { AlertTriangle, BrainCircuit, Sparkles, Target } from "lucide-react";

import { EmptyState } from "@/components/dashboard/EmptyState";
import { SectionCard } from "@/components/dashboard/SectionCard";
import type { AnalyticsInsightResponse } from "@/lib/schemas/finops";

type AnalyticsInsightPanelProps = {
  data?: AnalyticsInsightResponse;
  isLoading: boolean;
};

export function AnalyticsInsightPanel({ data, isLoading }: AnalyticsInsightPanelProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 xl:grid-cols-3">
        <div className="animate-pulse rounded-3xl bg-slate-200 p-6 h-[220px]" />
        <div className="animate-pulse rounded-3xl bg-slate-200 p-6 h-[220px]" />
        <div className="animate-pulse rounded-3xl bg-slate-200 p-6 h-[220px]" />
      </div>
    );
  }

  if (!data) {
    return <EmptyState title="Sem insights complementares" description="Não foi possível montar a camada narrativa para este recorte." />;
  }

  return (
    <section className="grid gap-4 xl:grid-cols-12">
      <div className="xl:col-span-5">
        <SectionCard
          title="AI Summary"
          description={`Camada complementar em modo ${data.mode === "llm" ? "LLM" : "heurístico"} sem alterar os números base.`}
        >
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800">
              <BrainCircuit className="h-3.5 w-3.5" />
              {data.mode === "llm" ? "LLM Enabled" : "Deterministic Fallback"}
            </div>
            <p className="text-sm leading-6 text-slate-600">{data.summary}</p>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              <p>
                <strong>Total do período:</strong> {data.evidence.totalPeriod.toFixed(2)}
              </p>
              <p>
                <strong>Delta:</strong> {data.evidence.deltaPeriodPct.toFixed(2)}%
              </p>
              <p>
                <strong>Pico:</strong> {data.evidence.peakDay ?? "n/d"}
              </p>
            </div>
          </div>
        </SectionCard>
      </div>

      <div className="xl:col-span-3">
        <InsightListCard title="Drivers" icon={<Sparkles className="h-4 w-4" />} items={data.drivers} tone="emerald" />
      </div>

      <div className="xl:col-span-4">
        <InsightListCard title="Watchouts" icon={<AlertTriangle className="h-4 w-4" />} items={data.risks} tone="amber" />
      </div>

      <div className="xl:col-span-7">
        <SectionCard title="Recommended Actions" description="Ações sugeridas para aprofundar a investigação.">
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

      <div className="xl:col-span-5">
        <SectionCard title="Suggested Questions" description="Perguntas úteis para a próxima iteração analítica.">
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
      </div>
    </section>
  );
}

function InsightListCard({
  title,
  items,
  icon,
  tone,
}: {
  title: string;
  items: string[];
  icon: React.ReactNode;
  tone: "emerald" | "amber";
}) {
  const toneClass =
    tone === "emerald"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : "border-amber-200 bg-amber-50 text-amber-800";

  return (
    <SectionCard title={title} description={`${title} inferidos a partir do payload analítico.`}>
      <div className="space-y-3">
        <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${toneClass}`}>{icon}{title}</div>
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
