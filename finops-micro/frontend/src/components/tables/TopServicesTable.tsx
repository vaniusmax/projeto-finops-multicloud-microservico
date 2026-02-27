"use client";

import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { useMemo } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatMoney, type Currency } from "@/lib/format";
import type { TopServicesResponse } from "@/lib/schemas/finops";

const columnHelper = createColumnHelper<TopServicesResponse[number]>();

type TopServicesTableProps = {
  data: TopServicesResponse;
  currency: Currency;
  title?: string;
};

export function TopServicesTable({ data, currency, title = "DADOS DO GRÁFICO DE LINHAS" }: TopServicesTableProps) {
  const rows = useMemo(() => data.slice(0, 10), [data]);
  const total = useMemo(() => rows.reduce((acc, row) => acc + row.total, 0), [rows]);

  const columns = [
    columnHelper.accessor("serviceName", {
      header: "Serviço",
      cell: (info) => info.getValue() ?? "N/A",
    }),
    columnHelper.accessor("total", {
      header: "Total",
      cell: (info) => <div className="text-right">{formatMoney(info.getValue(), currency)}</div>,
    }),
  ];

  const table = useReactTable({ data: rows, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <Card className="rounded-md border border-slate-200 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-3xl text-slate-900">{title}</CardTitle>
      </CardHeader>
      <CardContent className="max-h-[320px] overflow-y-auto p-0">
        <Table className="text-[11px]">
          <TableHeader>
            {table.getHeaderGroups().map((group) => (
              <TableRow key={group.id} className="hover:bg-transparent">
                {group.headers.map((header) => (
                  <TableHead key={header.id} className={`py-1.5 ${header.id.includes("total") ? "text-right" : ""}`}>
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} className="h-6">
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="py-1.5">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
            <TableRow className="h-6 font-semibold hover:bg-transparent">
              <TableCell className="py-1.5">TOTAL</TableCell>
              <TableCell className="py-1.5 text-right">{formatMoney(total, currency)}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
