"use client";

import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { useMemo } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatMoney, formatPctValue, type Currency } from "@/lib/format";
import type { OciTagCostResponse } from "@/lib/schemas/finops";

type OciTagCostGridRow = {
  tagValue: string;
  total: number;
  sharePct: number;
};

const columnHelper = createColumnHelper<OciTagCostGridRow>();

type OciTagCostGridProps = {
  data: OciTagCostResponse;
  currency: Currency;
  title?: string;
};

function toRows(data: OciTagCostResponse): OciTagCostGridRow[] {
  const totals = new Map<string, number>();

  for (const item of data.items) {
    for (const [tagValue, amount] of Object.entries(item.byTag ?? {})) {
      totals.set(tagValue, (totals.get(tagValue) ?? 0) + amount);
    }
  }

  return Array.from(totals.entries())
    .sort((a, b) => {
      if (a[0] === "Others") return 1;
      if (b[0] === "Others") return -1;
      return b[1] - a[1];
    })
    .map(([tagValue, total]) => ({
      tagValue,
      total,
      sharePct: data.totalPeriod > 0 ? (total / data.totalPeriod) * 100 : 0,
    }));
}

export function OciTagCostGrid({ data, currency, title = "TAG BREAKDOWN GRID" }: OciTagCostGridProps) {
  const rows = useMemo(() => toRows(data), [data]);
  const columns = [
    columnHelper.accessor("tagValue", {
      header: "TAG VALUE",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor("sharePct", {
      header: "SHARE",
      cell: (info) => <div className="text-right">{formatPctValue(info.getValue())}</div>,
    }),
    columnHelper.accessor("total", {
      header: "TOTAL",
      cell: (info) => <div className="text-right">{formatMoney(info.getValue(), currency)}</div>,
    }),
  ];

  const table = useReactTable({ data: rows, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <Card className="rounded-2xl border border-slate-200 bg-white shadow-soft">
      <CardHeader className="border-b border-slate-100 pb-4">
        <CardTitle className="text-lg font-semibold tracking-tight text-slate-900">{title}</CardTitle>
      </CardHeader>
      <CardContent className="max-h-[420px] overflow-y-auto p-0">
        <Table className="text-[12px]">
          <TableHeader>
            {table.getHeaderGroups().map((group) => (
              <TableRow key={group.id} className="hover:bg-transparent">
                {group.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className={`py-3 ${header.id.includes("sharePct") || header.id.includes("total") ? "text-right" : ""}`}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} className="h-11">
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="py-2.5">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
            <TableRow className="h-11 bg-slate-50 font-semibold hover:bg-slate-50">
              <TableCell className="py-3">TOTAL</TableCell>
              <TableCell className="py-3 text-right">100.0%</TableCell>
              <TableCell className="py-3 text-right">{formatMoney(data.totalPeriod, currency)}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
