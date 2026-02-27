export type Currency = "BRL" | "USD";

export function formatMoney(value: number, currency: Currency) {
  const locale = currency === "BRL" ? "pt-BR" : "en-US";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatCompactMoney(value: number, currency: Currency) {
  const abs = Math.abs(value);
  const symbol = currency === "BRL" ? "R$" : "US$";
  if (abs >= 1_000_000) {
    return `${symbol} ${(value / 1_000_000).toFixed(2).replace(".", ",")}M`;
  }
  if (abs >= 1_000) {
    return `${symbol} ${(value / 1_000).toFixed(2).replace(".", ",")}K`;
  }
  return formatMoney(value, currency);
}

export function formatNumber(value: number, fractionDigits = 4) {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

export function formatPct(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export function formatDateLabel(date: string) {
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit" }).format(
    new Date(`${date}T00:00:00`),
  );
}
