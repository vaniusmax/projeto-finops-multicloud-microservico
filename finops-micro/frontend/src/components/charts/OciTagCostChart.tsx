"use client";

import { memo, useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatMoney, type Currency } from "@/lib/format";
import type { OciTagCostResponse } from "@/lib/schemas/finops";

type OciTagCostChartProps = {
  data: OciTagCostResponse | undefined;
  currency: Currency;
  title?: string;
};

const COLORS = [
  "#d7263d",
  "#1b1f3b",
  "#19b5e4",
  "#0a8754",
  "#ffb703",
  "#6a4c93",
  "#e63946",
  "#00ad7c",
  "#7c4dff",
  "#f4b400",
  "#00a2d8",
  "#8d99ae",
];

function formatAxisDate(date: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
  }).format(new Date(`${date}T00:00:00`));
}

function OciTagCostChartComponent({
  data,
  currency,
  title = "COST BY DATE (UTC)",
}: OciTagCostChartProps) {
  const chartData = useMemo(
    () =>
      (data?.items ?? []).map((item) => ({
        date: item.date,
        ...item.byTag,
      })),
    [data],
  );

  const seriesOrder = useMemo(() => {
    if (!data) return [] as string[];
    const totals = new Map<string, number>();
    for (const row of data.items) {
      for (const [value, amount] of Object.entries(row.byTag ?? {})) {
        totals.set(value, (totals.get(value) ?? 0) + amount);
      }
    }
    const sorted = Array.from(totals.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([name]) => name);
    const others = sorted.filter((value) => value === "Others");
    const top = sorted.filter((value) => value !== "Others");
    return top.concat(others);
  }, [data]);

  return (
    <Card className="rounded-2xl border border-slate-200 bg-white shadow-soft">
      <CardHeader className="border-b border-slate-100 pb-4">
        <CardTitle className="text-lg font-semibold tracking-tight text-slate-900">
          {title}
        </CardTitle>
        <p className="text-xs text-slate-500">
          Custos diários do tenant {data?.tenantKey ?? "OCI"} agrupados pela tag{" "}
          <strong>
            {data?.tagNamespace ?? "operation"} / {data?.tagKey ?? "plataform"}
          </strong>
          .
        </p>
      </CardHeader>
      <CardContent className="h-[420px] p-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ left: 8, right: 8, top: 8, bottom: 60 }}>
            <CartesianGrid stroke="#e5e7eb" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatAxisDate}
              tick={{ fill: "#6b7280", fontSize: 10 }}
            />
            <YAxis
              tick={{ fill: "#6b7280", fontSize: 10 }}
              tickFormatter={(value) =>
                `${currency === "BRL" ? "R$" : "US$"} ${Math.round(Number(value)).toLocaleString("en-US")}`
              }
              label={{
                value: `Cost (${currency})`,
                angle: -90,
                position: "insideLeft",
                fill: "#6b7280",
                fontSize: 11,
              }}
            />
            <Tooltip
              labelFormatter={(value) => formatAxisDate(String(value))}
              formatter={(value: number, name: string) => [formatMoney(value, currency), name]}
            />
            <Legend wrapperStyle={{ bottom: -8, fontSize: "10px" }} />
            {seriesOrder.map((value, index) => (
              <Bar
                key={value}
                stackId="oci-tag"
                dataKey={value}
                fill={value === "Others" ? "#aab3c8" : COLORS[index % COLORS.length]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export const OciTagCostChart = memo(OciTagCostChartComponent);
