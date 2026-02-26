import { SummaryResponse, TimeseriesResponse, TopItem } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

type Query = {
  cloud: string;
  start: string;
  end: string;
  scope_key?: string;
  service_key?: string;
};

function toSearchParams(query: Query): URLSearchParams {
  const params = new URLSearchParams();
  params.set("cloud", query.cloud);
  params.set("start", query.start);
  params.set("end", query.end);
  if (query.scope_key) params.set("scope_key", query.scope_key);
  if (query.service_key) params.set("service_key", query.service_key);
  return params;
}

async function requestJson<T>(path: string, params: URLSearchParams): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}?${params.toString()}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Erro na API: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function fetchSummary(query: Query): Promise<SummaryResponse> {
  return requestJson<SummaryResponse>("/summary", toSearchParams(query));
}

export async function fetchTimeseries(query: Query): Promise<TimeseriesResponse> {
  const params = toSearchParams(query);
  params.set("granularity", "daily");
  return requestJson<TimeseriesResponse>("/timeseries", params);
}

export async function fetchTopServices(query: Query, limit = 10): Promise<TopItem[]> {
  const params = toSearchParams(query);
  params.set("limit", String(limit));
  return requestJson<TopItem[]>("/top-services", params);
}
