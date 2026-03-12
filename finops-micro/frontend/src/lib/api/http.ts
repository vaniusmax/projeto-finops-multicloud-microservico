import { mockRoute } from "@/lib/mocks/mock-api";
import { clearStoredAccessToken, getStoredAccessToken } from "@/lib/auth/storage";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

const gateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
const finopsService = process.env.NEXT_PUBLIC_FINOPS_SERVICE_URL;
const directBase = process.env.NEXT_PUBLIC_API_BASE_URL;
const apiBasePath = process.env.NEXT_PUBLIC_API_BASE_PATH ?? "/api/v1";

export const baseURL = gateway ?? finopsService ?? directBase ?? "";
const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS === "true" || !baseURL;

type RequestConfig = {
  method?: "GET" | "POST";
  path: string;
  query?: Record<string, string | number | undefined | string[]>;
  body?: unknown;
};

function buildUrl(path: string, query?: RequestConfig["query"]) {
  const fullPath = `${apiBasePath}${path}`.replace(/\/{2,}/g, "/");
  const url = new URL(fullPath, baseURL || "http://localhost:3000");
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (Array.isArray(value)) {
        value.forEach((v) => url.searchParams.append(key, v));
      } else if (value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url;
}

export async function request<T>({ method = "GET", path, query, body }: RequestConfig): Promise<T> {
  const url = buildUrl(path, query);

  if (useMocks) {
    return mockRoute<T>({ method, path: `${url.pathname}${url.search}`, body });
  }

  const headers: Record<string, string> = {};
  const accessToken = getStoredAccessToken();
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(url.toString(), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Falha na requisição: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Mantém a mensagem padrão quando a resposta não vier em JSON.
    }
    if (response.status === 401) {
      clearStoredAccessToken();
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}
