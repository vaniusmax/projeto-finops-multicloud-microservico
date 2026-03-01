import { request } from "@/lib/api/http";
import {
  aiInsightSchema,
  analyticsInsightSchema,
  costExplorerBreakdownSchema,
  costExplorerInsightSchema,
  costExplorerSnapshotSchema,
  costExplorerTrendSchema,
  dailySchema,
  filtersSchema,
  summarySchema,
  topAccountsSchema,
  topServicesSchema,
  type AiInsightResponse,
  type AnalyticsInsightResponse,
  type CostExplorerBreakdownResponse,
  type CostExplorerInsightResponse,
  type CostExplorerSnapshotResponse,
  type CostExplorerTrendResponse,
  type DailyResponse,
  type FiltersResponse,
  type SummaryResponse,
  type TopAccountsResponse,
  type TopServicesResponse,
} from "@/lib/schemas/finops";

type CommonFilters = {
  cloud: string;
  from: string;
  to: string;
  currency: "BRL" | "USD";
};

type DailyParams = CommonFilters & {
  topN?: number;
  services?: string[];
  accounts?: string[];
};

type TopParams = CommonFilters & {
  topN: number;
};

export async function getSummary(params: CommonFilters): Promise<SummaryResponse> {
  const data = await request<unknown>({ path: "/finops/summary", query: params });
  return summarySchema.parse(data);
}

export async function getDaily(params: DailyParams): Promise<DailyResponse> {
  const data = await request<unknown>({
    path: "/finops/daily",
    query: {
      ...params,
      topN: params.topN,
      services: params.services,
      accounts: params.accounts,
    },
  });
  return dailySchema.parse(data);
}

export async function getTopServices(params: TopParams): Promise<TopServicesResponse> {
  const data = await request<unknown>({ path: "/finops/top-services", query: params });
  return topServicesSchema.parse(data);
}

export async function getTopAccounts(params: TopParams): Promise<TopAccountsResponse> {
  const data = await request<unknown>({ path: "/finops/top-accounts", query: params });
  return topAccountsSchema.parse(data);
}

export async function getFilters(cloud: string, month: string): Promise<FiltersResponse> {
  const data = await request<unknown>({ path: "/finops/filters", query: { cloud, month } });
  return filtersSchema.parse(data);
}

export type AiInsightPayload = CommonFilters & {
  question: string;
  filters: {
    services: string[];
    accounts: string[];
  };
};

export async function postAiInsights(payload: AiInsightPayload): Promise<AiInsightResponse> {
  const data = await request<unknown>({
    method: "POST",
    path: "/finops/ai/insights",
    body: payload,
  });
  return aiInsightSchema.parse(data);
}

export type AnalyticsInsightPayload = CommonFilters & {
  topN: number;
  services?: string[];
  accounts?: string[];
};

export async function postAnalyticsInsights(payload: AnalyticsInsightPayload): Promise<AnalyticsInsightResponse> {
  const data = await request<unknown>({
    method: "POST",
    path: "/finops/analytics/insights",
    body: payload,
  });
  return analyticsInsightSchema.parse(data);
}

export type CostExplorerParams = CommonFilters & {
  topN: number;
  groupBy: "service" | "account";
  selectedItem?: string;
  services?: string[];
  accounts?: string[];
};

export async function getCostExplorerSnapshot(params: CostExplorerParams): Promise<CostExplorerSnapshotResponse> {
  const data = await request<unknown>({ path: "/finops/cost-explorer/snapshot", query: params });
  return costExplorerSnapshotSchema.parse(data);
}

export async function getCostExplorerBreakdown(params: CostExplorerParams): Promise<CostExplorerBreakdownResponse> {
  const data = await request<unknown>({ path: "/finops/cost-explorer/breakdown", query: params });
  return costExplorerBreakdownSchema.parse(data);
}

export async function getCostExplorerTrend(params: CostExplorerParams): Promise<CostExplorerTrendResponse> {
  const data = await request<unknown>({ path: "/finops/cost-explorer/trend", query: params });
  return costExplorerTrendSchema.parse(data);
}

export async function postCostExplorerInsights(payload: CostExplorerParams): Promise<CostExplorerInsightResponse> {
  const data = await request<unknown>({
    method: "POST",
    path: "/finops/cost-explorer/insights",
    body: payload,
  });
  return costExplorerInsightSchema.parse(data);
}

export type ReingestPayload = {
  cloud: string;
  from: string;
  to: string;
};

export async function postReingest(payload: ReingestPayload): Promise<{ results: Array<{ provider: string; rows_received: number; rows_written: number }> }> {
  return request({
    method: "POST",
    path: "/finops/reingest",
    body: payload,
  });
}
