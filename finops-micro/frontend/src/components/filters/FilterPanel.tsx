"use client";

import { Check, X } from "lucide-react";

import { DateRangePicker } from "@/components/filters/DateRangePicker";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DashboardFilters } from "@/lib/query/search-params";

type FilterPanelProps = {
  filters: DashboardFilters;
  services: string[];
  accounts: string[];
  onChange: (next: Partial<DashboardFilters>) => void;
};

function ToggleList({
  selected,
  options,
  onChange,
  label,
}: {
  selected: string[];
  options: string[];
  onChange: (values: string[]) => void;
  label: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-100">{label}</p>
      <div className="max-h-40 overflow-auto rounded-xl bg-white/10 p-2">
        <div className="mb-2 flex flex-wrap gap-1">
          {selected.map((item) => (
            <Badge key={item} className="gap-1 bg-emerald-200 text-emerald-900">
              {item}
              <button type="button" onClick={() => onChange(selected.filter((v) => v !== item))}>
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
        <div className="space-y-1">
          {options.map((item) => {
            const active = selected.includes(item);
            return (
              <button
                type="button"
                key={item}
                onClick={() => onChange(active ? selected.filter((v) => v !== item) : [...selected, item])}
                className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-xs ${
                  active ? "bg-emerald-100 text-emerald-900" : "text-white hover:bg-white/20"
                }`}
              >
                <span className="inline-flex h-4 w-4 items-center justify-center rounded border border-current">
                  {active ? <Check className="h-3 w-3" /> : null}
                </span>
                {item}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export function FilterPanel({ filters, services, accounts, onChange }: FilterPanelProps) {
  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-xs font-medium text-emerald-100">Cloud</label>
        <Select value={filters.cloud.toUpperCase()} onValueChange={(value) => onChange({ cloud: value.toLowerCase() })}>
          <SelectTrigger>
            <SelectValue placeholder="Selecione" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="AWS">AWS</SelectItem>
            <SelectItem value="AZURE">AZURE</SelectItem>
            <SelectItem value="OCI">OCI</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DateRangePicker
        from={filters.from}
        to={filters.to}
        onChange={(range) => onChange({ from: range.from, to: range.to })}
      />

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-100">Moeda</p>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant={filters.currency === "BRL" ? "secondary" : "outline"}
            onClick={() => onChange({ currency: "BRL" })}
          >
            BRL
          </Button>
          <Button
            size="sm"
            variant={filters.currency === "USD" ? "secondary" : "outline"}
            onClick={() => onChange({ currency: "USD" })}
          >
            USD
          </Button>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-emerald-100">Top N</label>
        <Input
          type="number"
          min={1}
          max={50}
          value={filters.topN}
          onChange={(e) => onChange({ topN: Number(e.target.value || 10) })}
        />
      </div>

      <ToggleList label="Serviços" options={services} selected={filters.services} onChange={(values) => onChange({ services: values })} />
      <ToggleList label="Linked Accounts" options={accounts} selected={filters.accounts} onChange={(values) => onChange({ accounts: values })} />
    </div>
  );
}
