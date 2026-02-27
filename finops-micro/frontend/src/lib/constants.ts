export const CLOUDS = ["AWS", "AZURE", "OCI"] as const;

export const DEFAULT_FILTERS = {
  cloud: "aws",
  from: "2026-02-16",
  to: "2026-02-22",
  currency: "BRL",
  topN: 10,
  services: [] as string[],
  accounts: [] as string[],
};
