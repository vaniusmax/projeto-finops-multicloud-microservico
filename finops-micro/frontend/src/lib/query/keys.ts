import type { DashboardFilters } from "@/lib/query/search-params";

export const finopsKeys = {
  summary: (filters: DashboardFilters) => ["finops", "summary", filters] as const,
  daily: (filters: DashboardFilters) => ["finops", "daily", filters] as const,
  topServices: (filters: DashboardFilters) => ["finops", "top-services", filters] as const,
  topAccounts: (filters: DashboardFilters) => ["finops", "top-accounts", filters] as const,
  filters: (cloud: string, month: string) => ["finops", "filters", cloud, month] as const,
};
