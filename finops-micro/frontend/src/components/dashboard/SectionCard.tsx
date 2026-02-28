"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type SectionCardProps = {
  title: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  contentClassName?: string;
};

export function SectionCard({ title, description, action, children, contentClassName }: SectionCardProps) {
  return (
    <Card className="rounded-2xl border border-slate-200 bg-white shadow-soft">
      <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <CardTitle className="text-lg font-semibold tracking-tight text-slate-900">{title}</CardTitle>
          {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
        </div>
        {action}
      </CardHeader>
      <CardContent className={contentClassName ?? "p-6"}>{children}</CardContent>
    </Card>
  );
}
