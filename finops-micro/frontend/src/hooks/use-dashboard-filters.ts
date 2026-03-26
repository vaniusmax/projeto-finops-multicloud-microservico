"use client";

import { useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { mergeSearchParams, parseFilters, type DashboardFilters } from "@/lib/query/search-params";

export function useDashboardFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const filters = useMemo(() => parseFilters(new URLSearchParams(searchParams.toString())), [searchParams]);

  function updateFilters(patch: Partial<DashboardFilters>) {
    const next: DashboardFilters = { ...filters, ...patch };
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
