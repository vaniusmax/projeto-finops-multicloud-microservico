"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getCostExplorerBreakdown,
  getCloudTenants,
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

const memoryFirstQueryOptions = {
  staleTime: 1000 * 60,
  gcTime: 1000 * 60 * 60,
  refetchOnWindowFocus: false,
  refetchOnReconnect: false,
} as const;

function isTenantReady(filters: DashboardFilters) {
  if (filters.cloud === "oci") {
    return Boolean(filters.tenant);
  }
  return true;
}

export function useSummaryQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.summary(filters),
    queryFn: () => getSummary(filters),
    ...memoryFirstQueryOptions,
    enabled: isTenantReady(filters),
  });
}

export function useDailyQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.daily(filters),
    queryFn: () => getDaily(filters),
    ...memoryFirstQueryOptions,
    enabled: isTenantReady(filters),
  });
}

export function useTopServicesQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.topServices(filters),
    queryFn: () => getTopServices(filters),
    ...memoryFirstQueryOptions,
    enabled: isTenantReady(filters),
  });
}

export function useTopAccountsQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.topAccounts(filters),
    queryFn: () => getTopAccounts(filters),
    ...memoryFirstQueryOptions,
    enabled: isTenantReady(filters),
  });
}

export function useAnalyticsInsightsQuery(filters: DashboardFilters) {
  return useQuery({
    queryKey: finopsKeys.analyticsInsights(filters),
    queryFn: () => postAnalyticsInsights(filters),
    ...memoryFirstQueryOptions,
    enabled: isTenantReady(filters),
  });
}

export function useCostExplorerSnapshotQuery(filters: DashboardFilters, groupBy: "service" | "account") {
  return useQuery({
    queryKey: finopsKeys.costExplorerSnapshot(filters, groupBy),
    queryFn: () => getCostExplorerSnapshot({ ...filters, groupBy }),
    ...memoryFirstQueryOptions,
    enabled: isTenantReady(filters),
  });
}

export function useCostExplorerBreakdownQuery(filters: DashboardFilters, groupBy: "service" | "account") {
  return useQuery({
    queryKey: finopsKeys.costExplorerBreakdown(filters, groupBy),
    queryFn: () => getCostExplorerBreakdown({ ...filters, groupBy }),
    ...memoryFirstQueryOptions,
    enabled: isTenantReady(filters),
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
    ...memoryFirstQueryOptions,
    enabled: enabled && isTenantReady(filters),
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
    ...memoryFirstQueryOptions,
    enabled: enabled && isTenantReady(filters),
  });
}

export function useFilterOptionsQuery(cloud: string, month: string, tenant: string, enabled = true) {
  return useQuery({
    queryKey: finopsKeys.filters(cloud, month, tenant),
    queryFn: () => getFilters(cloud, month, tenant),
    ...memoryFirstQueryOptions,
    enabled,
  });
}

export function useTenantOptionsQuery(cloud: string, enabled = true) {
  return useQuery({
    queryKey: finopsKeys.tenants(cloud),
    queryFn: () => getCloudTenants(cloud),
    ...memoryFirstQueryOptions,
    enabled: enabled && cloud !== "all",
  });
}
