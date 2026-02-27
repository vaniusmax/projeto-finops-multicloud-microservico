"use client";

import { memo, useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatMoney, type Currency } from "@/lib/format";
import type { DailyResponse } from "@/lib/schemas/finops";

type LineChartDailyProps = {
  data: DailyResponse;
  currency: Currency;
  title?: string;
};

const COLORS = ["#00C2FF", "#1b1f3b", "#6a4c93", "#0a8754", "#00ad7c", "#b4b000", "#ffb703", "#e63946", "#7c2e9c", "#8d99ae"];

function formatAxisDate(date: string) {
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(new Date(`${date}T00:00:00`));
}

function LineChartDailyComponent({ data, currency, title = "GRÁFICO DE LINHAS" }: LineChartDailyProps) {
  const seriesOrder = useMemo(() => {
    const totals = new Map<string, number>();
    for (const row of data) {
      for (const [service, value] of Object.entries(row.byService ?? {})) {
        totals.set(service, (totals.get(service) ?? 0) + value);
      }
    }
    const sorted = Array.from(totals.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([name]) => name);
    const hasOthers = sorted.includes("Others");
    const withoutOthers = sorted.filter((item) => item !== "Others");
    const fixedTop = withoutOthers.slice(0, hasOthers ? 9 : 10);
    return hasOthers ? fixedTop.concat("Others") : fixedTop;
  }, [data]);

  const chartData = useMemo(
    () =>
      data.map((item) => ({
        date: item.date,
        ...item.byService,
      })),
    [data],
  );

  return (
    <Card className="border-none shadow-none">
      <CardHeader className="px-0">
        <CardTitle className="text-3xl text-slate-900">{title}</CardTitle>
      </CardHeader>
      <CardContent className="h-[320px] px-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ left: 8, right: 8, top: 8, bottom: 44 }}>
            <CartesianGrid stroke="#e5e7eb" vertical={false} />
            <XAxis dataKey="date" tickFormatter={formatAxisDate} tick={{ fill: "#6b7280", fontSize: 10 }} />
            <YAxis
              tick={{ fill: "#6b7280", fontSize: 10 }}
              tickFormatter={(value) => `R$ ${Math.round(Number(value)).toLocaleString("en-US")}`}
              label={{ value: "Custo", angle: -90, position: "insideLeft", fill: "#6b7280", fontSize: 11 }}
            />
            <Tooltip
              labelFormatter={(value) => formatAxisDate(String(value))}
              formatter={(value: number) => formatMoney(value, currency)}
            />
            <Legend wrapperStyle={{ bottom: -8, fontSize: "10px" }} />
            {seriesOrder.map((service, index) => (
              <Line
                key={service}
                type="monotone"
                dataKey={service}
                stroke={service === "Others" ? "#aab3c8" : COLORS[index % COLORS.length]}
                strokeWidth={service === "Others" ? 2 : 2.2}
                strokeDasharray={service === "Others" ? "5 5" : "0"}
                dot={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export const LineChartDaily = memo(LineChartDailyComponent);
