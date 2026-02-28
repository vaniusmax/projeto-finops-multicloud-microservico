"use client";

import { usePathname } from "next/navigation";

import { FilterDrawer } from "@/components/layout/FilterDrawer";
import { SidebarNav } from "@/components/layout/SidebarNav";
import { Topbar } from "@/components/layout/Topbar";
import { AppProvider, useAppContext } from "@/contexts/AppContext";
import { useDashboardFilters } from "@/hooks/use-dashboard-filters";

type AppShellProps = {
  children: React.ReactNode;
  services?: string[];
  accounts?: string[];
  showAdvancedFilters?: boolean;
  healthLabel?: string;
};

export function AppShell({
  children,
  services = [],
  accounts = [],
  showAdvancedFilters = true,
  healthLabel,
}: AppShellProps) {
  const pathname = usePathname();
  const { filters, updateFilters } = useDashboardFilters();

  return (
    <AppProvider filters={filters} onUpdateFilters={updateFilters}>
      <ShellFrame pathname={pathname} services={services} accounts={accounts} showAdvancedFilters={showAdvancedFilters} healthLabel={healthLabel}>
        {children}
      </ShellFrame>
    </AppProvider>
  );
}

function ShellFrame({
  pathname,
  services = [],
  accounts = [],
  showAdvancedFilters,
  healthLabel,
  children,
}: AppShellProps & { pathname: string }) {
  const { isSidebarCollapsed } = useAppContext();

  return (
    <div className="min-h-screen bg-[#F4F6F7]">
      <SidebarNav pathname={pathname} />
      <div className={`min-h-screen transition-all ${isSidebarCollapsed ? "lg:pl-[88px]" : "lg:pl-[248px]"}`}>
        <Topbar showAdvancedFilters={showAdvancedFilters} healthLabel={healthLabel} />
        <main className="px-4 py-6 lg:px-8">{children}</main>
      </div>
      {showAdvancedFilters ? <FilterDrawer services={services} accounts={accounts} /> : null}
    </div>
  );
}
