"use client";

import { Bell, Cloud, RefreshCcw, Save, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { DateRangePicker } from "@/components/filters/DateRangePicker";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useAppContext } from "@/contexts/AppContext";

type TopbarProps = {
  showAdvancedFilters?: boolean;
  healthLabel?: string;
};

const CLOUD_OPTIONS = [
  { label: "All Clouds", value: "all" },
  { label: "AWS", value: "aws" },
  { label: "Azure", value: "azure" },
  { label: "OCI", value: "oci" },
] as const;

export function Topbar({ showAdvancedFilters = true, healthLabel = "Healthy" }: TopbarProps) {
  const queryClient = useQueryClient();
  const {
    filters,
    updateFilters,
    compareMode,
    setCompareMode,
    triggerRefresh,
    setFilterDrawerOpen,
    savedViews,
    saveCurrentView,
    applySavedView,
  } = useAppContext();
  const [viewName, setViewName] = useState("");

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-[#F4F6F7]/95 backdrop-blur">
      <div className="flex flex-col gap-4 px-4 py-4 lg:px-8">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-emerald-700">FinOps Multicloud</p>
            <div className="mt-1 flex flex-wrap items-center gap-3">
              <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Enterprise Cost Control Workspace</h2>
              <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                {healthLabel}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm">
              <Bell className="h-4 w-4 text-emerald-700" />
              <span className="text-slate-600">Health indicator</span>
            </div>

            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-2 py-2 shadow-sm">
              <input
                value={viewName}
                onChange={(event) => setViewName(event.target.value)}
                placeholder="Salvar view"
                className="w-28 border-none bg-transparent text-sm outline-none placeholder:text-slate-400"
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  saveCurrentView(viewName);
                  setViewName("");
                }}
                disabled={!viewName.trim()}
                className="text-emerald-700 hover:bg-emerald-50"
              >
                <Save className="mr-2 h-4 w-4" />
                Save
              </Button>
            </div>

            <Select onValueChange={applySavedView}>
              <SelectTrigger className="w-[180px] bg-white shadow-sm">
                <SelectValue placeholder="Saved Views" />
              </SelectTrigger>
              <SelectContent>
                {savedViews.length === 0 ? <SelectItem value="__empty" disabled>Nenhuma view salva</SelectItem> : null}
                {savedViews.map((view) => (
                  <SelectItem key={view.id} value={view.id}>
                    {view.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-soft xl:grid-cols-[1.1fr_1.4fr_0.8fr_1fr_auto_auto]">
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
            <label className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <Cloud className="h-3.5 w-3.5" />
              Cloud
            </label>
            <Select value={filters.cloud} onValueChange={(value) => updateFilters({ cloud: value })}>
              <SelectTrigger className="border-none bg-transparent px-0 shadow-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CLOUD_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">Período</label>
            <DateRangePicker from={filters.from} to={filters.to} onChange={(range) => updateFilters(range)} />
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">Moeda</label>
            <Select value={filters.currency} onValueChange={(value) => updateFilters({ currency: value as "BRL" | "USD" })}>
              <SelectTrigger className="border-none bg-transparent px-0 shadow-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BRL">BRL</SelectItem>
                <SelectItem value="USD">USD</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
            <div className="mb-2 flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Comparar</label>
              <Switch
                checked={compareMode !== "off"}
                onCheckedChange={(checked) => setCompareMode(checked ? "previous-period" : "off")}
                ariaLabel="Ativar comparativo"
              />
            </div>
            <Select
              value={compareMode}
              onValueChange={(value) => setCompareMode(value as "off" | "previous-period")}
              disabled={compareMode === "off"}
            >
              <SelectTrigger className="border-none bg-transparent px-0 shadow-none">
                <SelectValue placeholder="Período anterior" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="previous-period">Período anterior equivalente</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {showAdvancedFilters ? (
            <Button
              variant="outline"
              className="h-auto rounded-xl border-slate-200 bg-white px-4 py-3 text-slate-700 shadow-sm hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-800"
              onClick={() => setFilterDrawerOpen(true)}
            >
              <SlidersHorizontal className="mr-2 h-4 w-4" />
              Filtros
            </Button>
          ) : null}

          <Button
            className="h-auto rounded-xl bg-[#145A32] px-4 py-3 text-white hover:bg-[#1E8449]"
            onClick={() => {
              triggerRefresh();
              void queryClient.invalidateQueries();
            }}
          >
            <RefreshCcw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>
    </header>
  );
}
