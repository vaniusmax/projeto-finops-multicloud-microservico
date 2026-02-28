import { getDefaultFilters } from "@/lib/constants";

export type DashboardFilters = {
  cloud: string;
  from: string;
  to: string;
  currency: "BRL" | "USD";
  topN: number;
  services: string[];
  accounts: string[];
};

export type CompareMode = "off" | "previous-period";

export function parseFilters(searchParams: URLSearchParams): DashboardFilters {
  const defaults = getDefaultFilters();
  return {
    cloud: searchParams.get("cloud") ?? defaults.cloud,
    from: searchParams.get("from") ?? defaults.from,
    to: searchParams.get("to") ?? defaults.to,
    currency: searchParams.get("currency") === "USD" ? "USD" : "BRL",
    topN: Number(searchParams.get("topN") ?? defaults.topN),
    services: searchParams.get("services")?.split(",").filter(Boolean) ?? [],
    accounts: searchParams.get("accounts")?.split(",").filter(Boolean) ?? [],
  };
}

export function toSearchParams(filters: DashboardFilters): URLSearchParams {
  const params = new URLSearchParams();
  params.set("cloud", filters.cloud);
  params.set("from", filters.from);
  params.set("to", filters.to);
  params.set("currency", filters.currency);
  params.set("topN", String(filters.topN));
  if (filters.services.length > 0) {
    params.set("services", filters.services.join(","));
  }
  if (filters.accounts.length > 0) {
    params.set("accounts", filters.accounts.join(","));
  }
  return params;
}

export function mergeSearchParams(
  current: URLSearchParams,
  filters: DashboardFilters,
  extras?: Record<string, string | null | undefined>,
): URLSearchParams {
  const params = new URLSearchParams(current.toString());
  const filterParams = toSearchParams(filters);

  ["cloud", "from", "to", "currency", "topN", "services", "accounts"].forEach((key) => {
    params.delete(key);
  });

  filterParams.forEach((value, key) => {
    params.set(key, value);
  });

  if (extras) {
    Object.entries(extras).forEach(([key, value]) => {
      if (value === undefined) return;
      if (value === null || value === "") {
        params.delete(key);
        return;
      }
      params.set(key, value);
    });
  }

  return params;
}
