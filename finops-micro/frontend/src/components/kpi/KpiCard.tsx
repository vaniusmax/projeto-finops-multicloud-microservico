import { TrendingDown, TrendingUp } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCompactMoney, formatMoney, formatNumber, formatPct, type Currency } from "@/lib/format";

type KpiCardProps = {
  title: string;
  value: number | null | undefined;
  currency: Currency;
  delta?: number;
  selected?: boolean;
  onClick?: () => void;
  valueType?: "money" | "compact-money" | "number";
  fractionDigits?: number;
};

export function KpiCard({
  title,
  value,
  currency,
  delta,
  selected,
  onClick,
  valueType = "money",
  fractionDigits = 4,
}: KpiCardProps) {
  const positive = (delta ?? 0) >= 0;
  const displayValue =
    value === null || value === undefined
      ? "—"
      : valueType === "compact-money"
        ? formatCompactMoney(value, currency)
        : valueType === "number"
          ? formatNumber(value, fractionDigits)
          : formatMoney(value, currency);

  return (
    <Card
      className={`rounded-2xl border transition ${selected ? "border-emerald-300 bg-app-selected" : "border-slate-200"} ${
        onClick ? "cursor-pointer hover:border-emerald-300" : ""
      }`}
      onClick={onClick}
    >
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-[11px]">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-semibold text-slate-900">{displayValue}</p>
        {delta !== undefined ? (
          <div className={`mt-2 inline-flex items-center gap-1 text-xs ${positive ? "text-emerald-700" : "text-red-700"}`}>
            {positive ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
            {formatPct(delta)}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
