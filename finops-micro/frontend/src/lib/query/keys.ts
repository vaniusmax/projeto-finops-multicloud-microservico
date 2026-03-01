import type { DashboardFilters } from "@/lib/query/search-params";

export const finopsKeys = {
  summary: (filters: DashboardFilters) => ["finops", "summary", filters] as const,
  daily: (filters: DashboardFilters) => ["finops", "daily", filters] as const,
  topServices: (filters: DashboardFilters) => ["finops", "top-services", filters] as const,
  topAccounts: (filters: DashboardFilters) => ["finops", "top-accounts", filters] as const,
  analyticsInsights: (filters: DashboardFilters) => ["finops", "analytics-insights", filters] as const,
  costExplorerSnapshot: (filters: DashboardFilters, groupBy: string) => ["finops", "cost-explorer", "snapshot", filters, groupBy] as const,
  costExplorerBreakdown: (filters: DashboardFilters, groupBy: string) => ["finops", "cost-explorer", "breakdown", filters, groupBy] as const,
  costExplorerTrend: (filters: DashboardFilters, groupBy: string, selectedItem: string | null) =>
    ["finops", "cost-explorer", "trend", filters, groupBy, selectedItem] as const,
  costExplorerInsights: (filters: DashboardFilters, groupBy: string, selectedItem: string | null) =>
    ["finops", "cost-explorer", "insights", filters, groupBy, selectedItem] as const,
  filters: (cloud: string, month: string) => ["finops", "filters", cloud, month] as const,
};
