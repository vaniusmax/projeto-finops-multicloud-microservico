"use client";

import Link from "next/link";
import { BrainCircuit, ChartColumnBig, ChevronLeft, ChevronRight, LayoutGrid, LineChart, PanelLeft, Settings2, Wallet } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAppContext } from "@/contexts/AppContext";

const NAV_ITEMS = [
  { href: "/overview", label: "Overview", icon: LayoutGrid },
  { href: "/analytics", label: "Analytics", icon: ChartColumnBig },
  { href: "/cost-explorer", label: "Cost Explorer", icon: PanelLeft },
  { href: "/trends", label: "Trends", icon: LineChart },
  { href: "/budgets", label: "Budgets", icon: Wallet },
  { href: "/ai", label: "AI Insights", icon: BrainCircuit },
  { href: "/settings", label: "Settings", icon: Settings2 },
] as const;

type SidebarNavProps = {
  pathname: string;
};

export function SidebarNav({ pathname }: SidebarNavProps) {
  const { isSidebarCollapsed, setSidebarCollapsed } = useAppContext();

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 hidden border-r border-emerald-900/30 bg-[#145A32] px-3 py-5 text-white shadow-soft lg:block ${
        isSidebarCollapsed ? "w-[88px]" : "w-[248px]"
      }`}
    >
      <div className={`mb-8 flex items-center ${isSidebarCollapsed ? "justify-center" : "justify-between gap-3 px-2"}`}>
        <div className={`${isSidebarCollapsed ? "hidden" : "block"}`}>
          <p className="text-xs uppercase tracking-[0.3em] text-emerald-100/80">FinOps</p>
          <h1 className="font-semibold tracking-tight text-white">Multicloud</h1>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSidebarCollapsed(!isSidebarCollapsed)}
          className="border border-white/10 bg-white/5 text-white hover:bg-white/10"
          aria-label={isSidebarCollapsed ? "Expandir menu" : "Recolher menu"}
        >
          {isSidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      <nav className="space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`) || (item.href === "/overview" && pathname === "/dashboard");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group flex items-center rounded-xl transition ${
                isSidebarCollapsed ? "justify-center px-0 py-3" : "gap-3 px-3 py-3"
              } ${
                active
                  ? "bg-white/12 text-white shadow-[inset_3px_0_0_0_#A7F3D0]"
                  : "text-emerald-50/80 hover:bg-white/8 hover:text-white"
              }`}
              title={isSidebarCollapsed ? item.label : undefined}
            >
              <Icon className="h-5 w-5 shrink-0" />
              <span className={isSidebarCollapsed ? "hidden" : "text-sm font-medium"}>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
