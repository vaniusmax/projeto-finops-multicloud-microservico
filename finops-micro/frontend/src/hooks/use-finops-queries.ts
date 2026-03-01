"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getCostExplorerBreakdown,
  getCostExplorerSnapshot,
  getCostExplorerTrend,
  getDaily,
  getFilters,
  getSummary,
  getTopAccounts,
  getTopServices,
  postAnalyticsInsights,
  postCostExplorerInsights,
} from "@/lib/api/finops";
import { finopsKeys } from "@/lib/query/keys";
import type { DashboardFilters } from "@/lib/query/search-params";

const staleTime = 1000 * 60;

export function useSummaryQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.summary(filters),
    queryFn: () => getSummary(filters),
    staleTime,
  });
}

export function useDailyQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.daily(filters),
    queryFn: () => getDaily(filters),
    staleTime,
  });
}

export function useTopServicesQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.topServices(filters),
    queryFn: () => getTopServices(filters),
    staleTime,
  });
}

export function useTopAccountsQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.topAccounts(filters),
    queryFn: () => getTopAccounts(filters),
    staleTime,
  });
}

export function useAnalyticsInsightsQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.analyticsInsights(filters),
    queryFn: () => postAnalyticsInsights(filters),
    staleTime,
  });
}

export function useCostExplorerSnapshotQuery(filters: DashboardFilters, groupBy: "service" | "account") {
  return useQuery({
    queryKey: finopsKeys.costExplorerSnapshot(filters, groupBy),
    queryFn: () => getCostExplorerSnapshot({ ...filters, groupBy }),
    staleTime,
  });
}

export function useCostExplorerBreakdownQuery(filters: DashboardFilters, groupBy: "service" | "account") {
  return useQuery({
    queryKey: finopsKeys.costExplorerBreakdown(filters, groupBy),
    queryFn: () => getCostExplorerBreakdown({ ...filters, groupBy }),
    staleTime,
  });
}

export function useCostExplorerTrendQuery(
  filters: DashboardFilters,
  groupBy: "service" | "account",
  selectedItem: string | null,
  enabled = true,
) {
  return useQuery({
    queryKey: finopsKeys.costExplorerTrend(filters, groupBy, selectedItem),
    queryFn: () => getCostExplorerTrend({ ...filters, groupBy, selectedItem: selectedItem ?? undefined }),
    staleTime,
    enabled,
  });
}

export function useCostExplorerInsightsQuery(
  filters: DashboardFilters,
  groupBy: "service" | "account",
  selectedItem: string | null,
  enabled = true,
) {
  return useQuery({
    queryKey: finopsKeys.costExplorerInsights(filters, groupBy, selectedItem),
    queryFn: () => postCostExplorerInsights({ ...filters, groupBy, selectedItem: selectedItem ?? undefined }),
    staleTime,
    enabled,
  });
}

export function useFilterOptionsQuery(cloud: string, month: string, enabled = true) {
  return useQuery({
    queryKey: finopsKeys.filters(cloud, month),
    queryFn: () => getFilters(cloud, month),
    staleTime,
    enabled,
  });
}
