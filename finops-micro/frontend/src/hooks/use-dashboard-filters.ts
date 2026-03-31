"use client";

import { useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { getDefaultTenantForCloud } from "@/lib/tenant-policy";
import { mergeSearchParams, parseFilters, type DashboardFilters } from "@/lib/query/search-params";

export function useDashboardFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const filters = useMemo(() => parseFilters(new URLSearchParams(searchParams.toString())), [searchParams]);

  function updateFilters(patch: Partial<DashboardFilters>) {
    const nextCloud = patch.cloud ?? filters.cloud;
    const shouldResetTenantForCloudChange = patch.cloud !== undefined && patch.tenant === undefined;

    let nextTenant = patch.tenant ?? filters.tenant;
    if (shouldResetTenantForCloudChange) {
      nextTenant = getDefaultTenantForCloud(nextCloud);
    }
    if (nextCloud === "all") {
      nextTenant = "";
    }

    const next: DashboardFilters = { ...filters, ...patch, cloud: nextCloud, tenant: nextTenant };
    const params = mergeSearchParams(new URLSearchParams(searchParams.toString()), next);
    const nextQuery = params.toString();
    const currentQuery = searchParams.toString();
    if (nextQuery === currentQuery) {
      return;
    }
    router.push(`${pathname}?${nextQuery}`);
  }

  return { filters, updateFilters };
}
