import { DEFAULT_FILTERS } from "@/lib/constants";

export type DashboardFilters = {
  cloud: string;
  from: string;
  to: string;
  currency: "BRL" | "USD";
  topN: number;
  services: string[];
  accounts: string[];
};

export function parseFilters(searchParams: URLSearchParams): DashboardFilters {
  return {
    cloud: searchParams.get("cloud") ?? DEFAULT_FILTERS.cloud,
    from: searchParams.get("from") ?? DEFAULT_FILTERS.from,
    to: searchParams.get("to") ?? DEFAULT_FILTERS.to,
    currency: searchParams.get("currency") === "USD" ? "USD" : "BRL",
    topN: Number(searchParams.get("topN") ?? DEFAULT_FILTERS.topN),
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
