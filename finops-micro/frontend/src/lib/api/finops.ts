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
  tenantsSchema,
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
  type TenantsResponse,
  type TopAccountsResponse,
  type TopServicesResponse,
} from "@/lib/schemas/finops";

type CommonFilters = {
  cloud: string;
  tenant: string;
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
  const { tenant, ...query } = params;
  const data = await request<unknown>({ path: "/finops/summary", query: { ...query, tenant_key: tenant || undefined } });
  return summarySchema.parse(data);
}

export async function getDaily(params: DailyParams): Promise<DailyResponse> {
  const { tenant, ...query } = params;
  const data = await request<unknown>({
    path: "/finops/daily",
    query: {
      ...query,
      tenant_key: tenant || undefined,
      topN: query.topN,
      services: query.services,
      accounts: query.accounts,
    },
  });
  return dailySchema.parse(data);
}

export async function getTopServices(params: TopParams): Promise<TopServicesResponse> {
  const { tenant, ...query } = params;
  const data = await request<unknown>({ path: "/finops/top-services", query: { ...query, tenant_key: tenant || undefined } });
  return topServicesSchema.parse(data);
}

export async function getTopAccounts(params: TopParams): Promise<TopAccountsResponse> {
  const { tenant, ...query } = params;
  const data = await request<unknown>({ path: "/finops/top-accounts", query: { ...query, tenant_key: tenant || undefined } });
  return topAccountsSchema.parse(data);
}

export async function getFilters(cloud: string, month: string, tenant: string): Promise<FiltersResponse> {
  const data = await request<unknown>({ path: "/finops/filters", query: { cloud, month, tenant_key: tenant || undefined } });
  return filtersSchema.parse(data);
}

export async function getCloudTenants(cloud: string): Promise<TenantsResponse> {
  const data = await request<unknown>({ path: `/cloud/${cloud}/tenants` });
  return tenantsSchema.parse(data);
}

export type AiInsightPayload = CommonFilters & {
  question: string;
  filters: {
    services: string[];
    accounts: string[];
  };
};

export async function postAiInsights(payload: AiInsightPayload): Promise<AiInsightResponse> {
  const { tenant, ...body } = payload;
  const data = await request<unknown>({
    method: "POST",
    path: "/finops/ai/insights",
    body: { ...body, tenant_key: tenant || undefined },
  });
  return aiInsightSchema.parse(data);
}

export type AnalyticsInsightPayload = CommonFilters & {
  topN: number;
  services?: string[];
  accounts?: string[];
};

export async function postAnalyticsInsights(payload: AnalyticsInsightPayload): Promise<AnalyticsInsightResponse> {
  const { tenant, ...body } = payload;
  const data = await request<unknown>({
    method: "POST",
    path: "/finops/analytics/insights",
    body: { ...body, tenant_key: tenant || undefined },
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
  const { tenant, ...query } = params;
  const data = await request<unknown>({
    path: "/finops/cost-explorer/snapshot",
    query: { ...query, tenant_key: tenant || undefined },
  });
  return costExplorerSnapshotSchema.parse(data);
}

export async function getCostExplorerBreakdown(params: CostExplorerParams): Promise<CostExplorerBreakdownResponse> {
  const { tenant, ...query } = params;
  const data = await request<unknown>({
    path: "/finops/cost-explorer/breakdown",
    query: { ...query, tenant_key: tenant || undefined },
  });
  return costExplorerBreakdownSchema.parse(data);
}

export async function getCostExplorerTrend(params: CostExplorerParams): Promise<CostExplorerTrendResponse> {
  const { tenant, ...query } = params;
  const data = await request<unknown>({
    path: "/finops/cost-explorer/trend",
    query: { ...query, tenant_key: tenant || undefined },
  });
  return costExplorerTrendSchema.parse(data);
}

export async function postCostExplorerInsights(payload: CostExplorerParams): Promise<CostExplorerInsightResponse> {
  const { tenant, ...body } = payload;
  const data = await request<unknown>({
    method: "POST",
    path: "/finops/cost-explorer/insights",
    body: { ...body, tenant_key: tenant || undefined },
  });
  return costExplorerInsightSchema.parse(data);
}

export type ReingestPayload = {
  cloud: string;
  tenant: string;
  from: string;
  to: string;
};

export async function postReingest(payload: ReingestPayload): Promise<{ results: Array<{ provider: string; rows_received: number; rows_written: number }> }> {
  const { tenant, ...body } = payload;
  return request({
    method: "POST",
    path: "/finops/reingest",
    body: { ...body, tenant_key: tenant || undefined },
  });
}
