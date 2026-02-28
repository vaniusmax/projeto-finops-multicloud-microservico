"use client";

import { Check, SlidersHorizontal, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAppContext } from "@/contexts/AppContext";

type FilterDrawerProps = {
  services: string[];
  accounts: string[];
};

function ToggleGroup({
  title,
  options,
  selected,
  onChange,
}: {
  title: string;
  options: string[];
  selected: string[];
  onChange: (values: string[]) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-800">{title}</p>
        {selected.length > 0 ? (
          <button type="button" className="text-xs text-emerald-700" onClick={() => onChange([])}>
            Limpar
          </button>
        ) : null}
      </div>
      <div className="max-h-56 space-y-1 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-2">
        {options.map((item) => {
          const active = selected.includes(item);
          return (
            <button
              type="button"
              key={item}
              onClick={() => onChange(active ? selected.filter((entry) => entry !== item) : [...selected, item])}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition ${
                active ? "bg-emerald-50 text-emerald-900" : "text-slate-600 hover:bg-white hover:text-slate-900"
              }`}
            >
              <span className={`inline-flex h-4 w-4 items-center justify-center rounded border ${active ? "border-emerald-700 bg-emerald-700 text-white" : "border-slate-300"}`}>
                {active ? <Check className="h-3 w-3" /> : null}
              </span>
              <span className="truncate">{item}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function FilterDrawer({ services, accounts }: FilterDrawerProps) {
  const { filters, updateFilters, isFilterDrawerOpen, setFilterDrawerOpen } = useAppContext();

  if (!isFilterDrawerOpen) return null;

  return (
    <div className="fixed inset-0 z-[70] bg-slate-950/30 backdrop-blur-[1px]">
      <div className="absolute inset-y-0 right-0 w-full max-w-[420px] border-l border-slate-200 bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-50 p-2 text-emerald-700">
              <SlidersHorizontal className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-900">Filtros avançados</h2>
              <p className="text-sm text-slate-500">Serviços, contas e granularidade analítica.</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={() => setFilterDrawerOpen(false)} aria-label="Fechar filtros">
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="space-y-5 overflow-y-auto p-5">
          <Card className="rounded-xl border border-slate-200 shadow-none">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Escopo de análise</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">Top N</label>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={filters.topN}
                  onChange={(event) => updateFilters({ topN: Number(event.target.value || 10) })}
                />
              </div>
            </CardContent>
          </Card>

          <ToggleGroup title="Serviços" options={services} selected={filters.services} onChange={(values) => updateFilters({ services: values })} />
          <ToggleGroup title="Linked Accounts" options={accounts} selected={filters.accounts} onChange={(values) => updateFilters({ accounts: values })} />
        </div>
      </div>
    </div>
  );
}
