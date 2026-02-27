"use client";

import { Menu } from "lucide-react";
import { useState } from "react";

import { FilterPanel } from "@/components/filters/FilterPanel";
import { Button } from "@/components/ui/button";
import type { DashboardFilters } from "@/lib/query/search-params";

type SidebarProps = {
  filters: DashboardFilters;
  services: string[];
  accounts: string[];
  onFiltersChange: (next: Partial<DashboardFilters>) => void;
};

export function Sidebar({ filters, services, accounts, onFiltersChange }: SidebarProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button
        variant="secondary"
        size="icon"
        onClick={() => setOpen(true)}
        className="fixed left-4 top-4 z-40 md:hidden"
        aria-label="Abrir filtros"
      >
        <Menu className="h-5 w-5" />
      </Button>

      <aside className="hidden w-[300px] shrink-0 bg-gradient-to-b from-app-sidebarFrom via-app-sidebarVia to-app-sidebarTo p-6 text-white md:fixed md:inset-y-0 md:left-0 md:block">
        <h2 className="text-2xl font-extrabold tracking-wide">FINOPS MULTICLOUD</h2>
        <p className="mb-6 mt-2 text-xs text-emerald-100">Selecione filtros para carregar dados</p>
        <FilterPanel filters={filters} services={services} accounts={accounts} onChange={onFiltersChange} />
      </aside>

      {open ? (
        <div className="fixed inset-0 z-50 bg-black/50 md:hidden">
          <aside className="h-full w-[90%] max-w-[320px] overflow-auto bg-gradient-to-b from-app-sidebarFrom via-app-sidebarVia to-app-sidebarTo p-6 text-white">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">FINOPS MULTICLOUD</h2>
              <Button variant="ghost" onClick={() => setOpen(false)} className="text-white hover:bg-white/20">
                Fechar
              </Button>
            </div>
            <FilterPanel
              filters={filters}
              services={services}
              accounts={accounts}
              onChange={(next) => {
                onFiltersChange(next);
              }}
            />
          </aside>
        </div>
      ) : null}
    </>
  );
}
