"use client";

import { useEffect, useMemo } from "react";
import { usePathname } from "next/navigation";

import { FilterDrawer } from "@/components/layout/FilterDrawer";
import { SidebarNav } from "@/components/layout/SidebarNav";
import { Topbar } from "@/components/layout/Topbar";
import { AppProvider, useAppContext } from "@/contexts/AppContext";
import { useDashboardFilters } from "@/hooks/use-dashboard-filters";
import { useTenantOptionsQuery } from "@/hooks/use-finops-queries";

type AppShellProps = {
  children: React.ReactNode;
  showAdvancedFilters?: boolean;
  healthLabel?: string;
};

export function AppShell({
  children,
  showAdvancedFilters = true,
  healthLabel,
}: AppShellProps) {
  const pathname = usePathname();
  const { filters, updateFilters } = useDashboardFilters();

  return (
    <AppProvider filters={filters} onUpdateFilters={updateFilters}>
      <ShellFrame pathname={pathname} showAdvancedFilters={showAdvancedFilters} healthLabel={healthLabel}>
        {children}
      </ShellFrame>
    </AppProvider>
  );
}

function ShellFrame({
  pathname,
  showAdvancedFilters,
  healthLabel,
  children,
}: AppShellProps & { pathname: string }) {
  const { isSidebarCollapsed, filters, updateFilters } = useAppContext();
  const tenantOptionsQuery = useTenantOptionsQuery(filters.cloud, filters.cloud !== "all");
  const tenantOptions = useMemo(() => tenantOptionsQuery.data ?? [], [tenantOptionsQuery.data]);
  const isTenantBootstrapPending =
    filters.cloud !== "all" && !filters.tenant && (tenantOptionsQuery.isLoading || tenantOptionsQuery.isFetching);
  const tenantExists = tenantOptions.some((item) => item.tenantKey === filters.tenant);
  const needsTenantSelection = filters.cloud !== "all" && tenantOptions.length > 0 && !tenantExists;
  const shouldHoldContent = isTenantBootstrapPending || needsTenantSelection;

  useEffect(() => {
    if (!needsTenantSelection) {
      return;
    }
    const firstTenant = tenantOptions[0]?.tenantKey ?? "";
    if (firstTenant && firstTenant !== filters.tenant) {
      updateFilters({ tenant: firstTenant });
    }
  }, [filters.tenant, needsTenantSelection, tenantOptions, updateFilters]);

  return (
    <div className="min-h-screen bg-[#F4F6F7]">
      <SidebarNav pathname={pathname} />
      <div className={`min-h-screen transition-all ${isSidebarCollapsed ? "lg:pl-[88px]" : "lg:pl-[248px]"}`}>
        <Topbar showAdvancedFilters={showAdvancedFilters} healthLabel={healthLabel} />
        <main className="px-4 py-6 lg:px-8">
          {shouldHoldContent ? <div className="min-h-[240px] rounded-3xl border border-slate-200 bg-white" /> : children}
        </main>
      </div>
      {showAdvancedFilters ? <FilterDrawer /> : null}
    </div>
  );
}
