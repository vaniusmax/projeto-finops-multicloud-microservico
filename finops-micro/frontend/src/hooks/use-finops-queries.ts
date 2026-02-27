"use client";

import { useQuery } from "@tanstack/react-query";

import { getDaily, getFilters, getSummary, getTopAccounts, getTopServices } from "@/lib/api/finops";
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

export function useFilterOptionsQuery(cloud: string, month: string) {
  return useQuery({
    queryKey: finopsKeys.filters(cloud, month),
    queryFn: () => getFilters(cloud, month),
    staleTime,
  });
}
