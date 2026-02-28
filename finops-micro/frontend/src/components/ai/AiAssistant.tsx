"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { postAiInsights } from "@/lib/api/finops";
import type { DashboardFilters } from "@/lib/query/search-params";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type Message = {
  role: "user" | "assistant";
  text: string;
  bullets?: string[];
};

type AiAssistantProps = {
  filters: DashboardFilters;
};

export function AiAssistant({ filters }: AiAssistantProps) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);

  const mutation = useMutation({
    mutationFn: postAiInsights,
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answerMarkdown,
          bullets: [...data.highlights, ...data.suggestedActions],
        },
      ]);
    },
  });

  function onAsk() {
    if (!question.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    mutation.mutate({
      cloud: filters.cloud,
      from: filters.from,
      to: filters.to,
      currency: filters.currency,
      question,
      filters: {
        services: filters.services,
        accounts: filters.accounts,
      },
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
              <p>{message.text}</p>
              {message.bullets?.length ? (
                <ul className="mt-2 list-disc space-y-1 pl-4 text-xs">
                  {message.bullets.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))}
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
