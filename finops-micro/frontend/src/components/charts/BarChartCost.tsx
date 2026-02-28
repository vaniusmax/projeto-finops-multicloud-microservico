"use client";

import { memo, useMemo } from "react";
import { Camera, Download, Search, ZoomIn, ZoomOut } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Currency } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatMoney } from "@/lib/format";
import type { TopAccountsResponse } from "@/lib/schemas/finops";

type BarChartCostProps = {
  data: TopAccountsResponse;
  currency: Currency;
  chartType?: "bar" | "line" | "pie";
};

const COLORS = ["#d7263d", "#ffb703", "#19b5e4", "#6a4c93", "#1b1f3b", "#e63946", "#f4b400", "#00a2d8", "#7c4dff", "#8d99ae"];

function BarChartCostComponent({ data, currency, chartType = "bar" }: BarChartCostProps) {
  const chartData = useMemo(
    () => data.slice(0, 10).map((item) => ({ name: item.linkedAccount ?? "N/A", total: Number(item.total.toFixed(2)) })),
    [data],
  );

  return (
    <Card className="border-none shadow-none">
      <CardHeader className="flex-row items-center justify-between px-0 pb-0">
        <CardTitle className="text-3xl tracking-normal text-slate-900">ANÁLISE DE DADOS</CardTitle>
        <div className="hidden items-center gap-1 text-slate-400 lg:flex">
          <Camera className="h-3.5 w-3.5" />
          <Search className="h-3.5 w-3.5" />
          <ZoomIn className="h-3.5 w-3.5" />
          <ZoomOut className="h-3.5 w-3.5" />
          <Download className="h-3.5 w-3.5" />
        </div>
      </CardHeader>
      <CardContent className="h-[320px] px-0">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "pie" ? (
            <PieChart>
              <Tooltip formatter={(value: number) => formatMoney(value, currency)} />
              <Legend />
              <Pie data={chartData} dataKey="total" nameKey="name" outerRadius={100}>
                {chartData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          ) : chartType === "line" ? (
            <LineChart data={chartData} margin={{ left: 4, right: 8, top: 8, bottom: 64 }}>
              <CartesianGrid vertical={false} stroke="#e5e7eb" />
              <XAxis dataKey="name" angle={-35} textAnchor="end" interval={0} height={66} tick={{ fill: "#6b7280", fontSize: 10 }} />
              <YAxis
                tick={{ fill: "#6b7280", fontSize: 10 }}
                tickFormatter={(value) => `R$ ${Math.round(Number(value)).toLocaleString("en-US")}`}
                label={{ value: "Custo", angle: -90, position: "insideLeft", fill: "#6b7280", fontSize: 11 }}
              />
              <Tooltip formatter={(value: number) => formatMoney(value, currency)} />
              <Line type="monotone" dataKey="total" stroke="#d7263d" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          ) : (
            <BarChart data={chartData} margin={{ left: 4, right: 8, top: 8, bottom: 64 }}>
              <CartesianGrid vertical={false} stroke="#e5e7eb" />
              <XAxis dataKey="name" angle={-35} textAnchor="end" interval={0} height={66} tick={{ fill: "#6b7280", fontSize: 10 }} />
              <YAxis
                tick={{ fill: "#6b7280", fontSize: 10 }}
                tickFormatter={(value) => `R$ ${Math.round(Number(value)).toLocaleString("en-US")}`}
                label={{ value: "Custo", angle: -90, position: "insideLeft", fill: "#6b7280", fontSize: 11 }}
              />
              <Tooltip formatter={(value: number) => formatMoney(value, currency)} />
              <Bar dataKey="total" radius={[0, 0, 0, 0]}>
                {chartData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export const BarChartCost = memo(BarChartCostComponent);
