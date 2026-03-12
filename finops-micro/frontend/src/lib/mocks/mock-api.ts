import { mockAiInsight, mockDaily, mockFilters, mockSummary, mockTenants, mockTopAccounts, mockTopServices } from "@/lib/mocks/fixtures";

function delay(ms = 350) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

type MockRouteRequest = {
  method: "GET" | "POST";
  path: string;
  body?: unknown;
};

const mockUser = {
  userId: "user-1",
  firstName: "Vanius",
  lastName: "Silva",
  email: "vanius@algar.com.br",
  isEmailVerified: true,
};

export async function mockRoute<T>({ path }: MockRouteRequest): Promise<T> {
  await delay();
  const url = new URL(path, "http://localhost");
  const topN = Number(url.searchParams.get("topN") ?? "10");

  if (url.pathname.includes("/auth/register")) {
    return {
      status: "pending_verification",
      email: "vanius@algar.com.br",
      message: "Enviamos um e-mail para concluir seu cadastro no dashboard.",
    } as T;
  }
  if (url.pathname.includes("/auth/login") || url.pathname.includes("/auth/verify-email")) {
    return {
      accessToken: "mock-token",
      expiresAt: new Date().toISOString(),
      user: mockUser,
    } as T;
  }
  if (url.pathname.includes("/auth/me")) return mockUser as T;
  if (url.pathname.includes("/auth/logout")) return undefined as T;
  if (url.pathname.includes("/finops/summary")) return mockSummary as T;
  if (url.pathname.includes("/finops/daily")) return mockDaily as T;
  if (url.pathname.includes("/finops/top-services")) return mockTopServices.slice(0, topN) as T;
  if (url.pathname.includes("/finops/top-accounts")) return mockTopAccounts.slice(0, topN) as T;
  if (url.pathname.includes("/finops/filters")) return mockFilters as T;
  if (url.pathname.includes("/cloud/") && url.pathname.includes("/tenants")) return mockTenants as T;
  if (url.pathname.includes("/finops/ai/insights")) return mockAiInsight as T;

  throw new Error(`Mock route not implemented for ${url.pathname}`);
}
