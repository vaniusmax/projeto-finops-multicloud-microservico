"use client";

import { AppShell } from "@/components/layout/AppShell";
import { useDashboardFilters } from "@/hooks/use-dashboard-filters";
import { useFilterOptionsQuery } from "@/hooks/use-finops-queries";

type WorkspacePageProps = {
  children: React.ReactNode;
  showAdvancedFilters?: boolean;
  healthLabel?: string;
};

export function WorkspacePage({ children, showAdvancedFilters = true, healthLabel }: WorkspacePageProps) {
  const { filters } = useDashboardFilters();
  const month = filters.from.slice(0, 7);
  const filterOptions = useFilterOptionsQuery(filters.cloud, month);

  return (
    <AppShell
      services={filterOptions.data?.services ?? []}
      accounts={filterOptions.data?.accounts ?? []}
      showAdvancedFilters={showAdvancedFilters}
      healthLabel={healthLabel}
    >
      {children}
    </AppShell>
  );
}
