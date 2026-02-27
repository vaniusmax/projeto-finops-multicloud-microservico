import { mockAiInsight, mockDaily, mockFilters, mockSummary, mockTopAccounts, mockTopServices } from "@/lib/mocks/fixtures";

function delay(ms = 350) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function mockRoute<T>(path: string): Promise<T> {
  await delay();
  const url = new URL(path, "http://localhost");
  const topN = Number(url.searchParams.get("topN") ?? "10");

  if (url.pathname.includes("/finops/summary")) return mockSummary as T;
  if (url.pathname.includes("/finops/daily")) return mockDaily as T;
  if (url.pathname.includes("/finops/top-services")) return mockTopServices.slice(0, topN) as T;
  if (url.pathname.includes("/finops/top-accounts")) return mockTopAccounts.slice(0, topN) as T;
  if (url.pathname.includes("/finops/filters")) return mockFilters as T;
  if (url.pathname.includes("/finops/ai/insights")) return mockAiInsight as T;

  throw new Error(`Mock route not implemented for ${url.pathname}`);
}
