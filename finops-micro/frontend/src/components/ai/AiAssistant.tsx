"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { postAiInsights } from "@/lib/api/finops";
import { ApiError } from "@/lib/api/http";
import type { DashboardFilters } from "@/lib/query/search-params";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type Message = {
  role: "user" | "assistant";
  text: string;
  highlights?: string[];
  actions?: string[];
};

type AiAssistantProps = {
  filters: DashboardFilters;
};

export function AiAssistant({ filters }: AiAssistantProps) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);

  function dedupe(items: string[]) {
    const seen = new Set<string>();
    return items.filter((item) => {
      const key = item.trim().toLowerCase();
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  const mutation = useMutation({
    mutationFn: postAiInsights,
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answerMarkdown,
          highlights: dedupe(data.highlights),
          actions: dedupe(data.suggestedActions),
        },
      ]);
    },
    onError: (error) => {
      const detail =
        error instanceof ApiError
          ? error.message
          : "Nao foi possivel consultar o assistente com os dados atuais. Tente novamente.";
      setMessages((prev) => [...prev, { role: "assistant", text: detail }]);
    },
  });

  function onAsk() {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || mutation.isPending) return;

    const history = [...messages.slice(-7), { role: "user" as const, text: trimmedQuestion }].map(({ role, text }) => ({
      role,
      text,
    }));

    setMessages((prev) => [...prev, { role: "user", text: trimmedQuestion }]);
    mutation.mutate({
      cloud: filters.cloud,
      tenant: filters.tenant,
      from: filters.from,
      to: filters.to,
      currency: filters.currency,
      topN: filters.topN,
      services: filters.services,
      accounts: filters.accounts,
      question: trimmedQuestion,
      history,
    });
    setQuestion("");
  }

  return (
    <Card className="rounded-2xl border border-slate-200 bg-white shadow-soft">
      <CardHeader className="border-b border-slate-100 pb-4">
        <CardTitle className="text-lg font-semibold tracking-tight text-slate-900">AI Assistant</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 h-[420px] space-y-3 overflow-auto rounded-2xl border border-slate-200 bg-slate-50 p-4">
          {messages.length === 0 ? (
            <p className="text-sm text-slate-500">Faça uma pergunta sobre custos, variações ou otimizações.</p>
          ) : null}
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`rounded-xl px-3 py-2 text-sm ${
                message.role === "user" ? "ml-10 bg-emerald-700 text-white shadow-sm" : "mr-10 border border-slate-200 bg-white text-slate-800"
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{message.text}</p>
              {message.highlights?.length ? (
                <div className="mt-3">
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Pontos-chave</p>
                  <ul className="list-disc space-y-1 pl-4 text-xs">
                    {message.highlights.map((item) => (
                      <li key={`h-${item}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {message.actions?.length ? (
                <div className="mt-3">
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Ações recomendadas</p>
                  <ul className="list-disc space-y-1 pl-4 text-xs">
                    {message.actions.map((item) => (
                      <li key={`a-${item}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ))}
          {mutation.isPending ? (
            <div className="mr-10 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500">Analisando os dados...</div>
          ) : null}
        </div>
        <div className="flex gap-2">
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ex.: Qual serviço mais contribuiu para o pico semanal?"
            onKeyDown={(e) => {
              if (e.key === "Enter") onAsk();
            }}
          />
          <Button onClick={onAsk} disabled={mutation.isPending}>
            {mutation.isPending ? "Enviando..." : "Perguntar"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
