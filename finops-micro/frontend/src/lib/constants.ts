export const CLOUDS = ["AWS", "AZURE", "OCI"] as const;

function toIso(day: Date) {
  const year = day.getFullYear();
  const month = String(day.getMonth() + 1).padStart(2, "0");
  const date = String(day.getDate()).padStart(2, "0");
  return `${year}-${month}-${date}`;
}

export function getDefaultFilters() {
  const today = new Date();
  const from = new Date(today);
  from.setDate(today.getDate() - 6);
  return {
    cloud: "aws",
    from: toIso(from),
    to: toIso(today),
    currency: "BRL" as const,
    topN: 10,
    services: [] as string[],
    accounts: [] as string[],
  };
}
