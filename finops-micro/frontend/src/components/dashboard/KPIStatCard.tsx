"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { formatCompactMoney, formatMoney, formatNumber, formatPct, type Currency } from "@/lib/format";

type KPIStatCardProps = {
  title: string;
  value: number | null | undefined;
  currency: Currency;
  delta?: number;
  tone?: "default" | "hero";
  valueType?: "money" | "compact-money" | "number";
  subtitle?: string;
  onClick?: () => void;
};

export function KPIStatCard({
  title,
  value,
  currency,
  delta,
  tone = "default",
  valueType = "money",
  subtitle,
  onClick,
}: KPIStatCardProps) {
  const displayValue =
    value == null
      ? "—"
      : valueType === "compact-money"
        ? formatCompactMoney(value, currency)
        : valueType === "number"
          ? formatNumber(value)
          : formatMoney(value, currency);
  const positive = (delta ?? 0) >= 0;

  return (
    <Card
      onClick={onClick}
      className={`rounded-2xl border shadow-soft transition ${
        tone === "hero"
          ? "border-emerald-200 bg-[linear-gradient(135deg,#145A32_0%,#1E8449_100%)] text-white"
          : "border-slate-200 bg-white text-slate-900"
      } ${onClick ? "cursor-pointer hover:-translate-y-0.5" : ""}`}
    >
      <CardHeader className="pb-2">
        <p className={`text-xs font-semibold uppercase tracking-[0.22em] ${tone === "hero" ? "text-emerald-100" : "text-slate-500"}`}>{title}</p>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className={`font-semibold tracking-tight ${tone === "hero" ? "text-3xl" : "text-2xl"}`}>{displayValue}</div>
        <div className="flex items-center justify-between gap-3">
          {subtitle ? <p className={`text-sm ${tone === "hero" ? "text-emerald-50/80" : "text-slate-500"}`}>{subtitle}</p> : <span />}
          {delta !== undefined ? (
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${
                tone === "hero"
                  ? "bg-white/10 text-white"
                  : positive
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-rose-50 text-rose-700"
              }`}
            >
              {positive ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
              {formatPct(delta)}
            </span>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
