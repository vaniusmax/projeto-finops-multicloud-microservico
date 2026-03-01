"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InfoHint } from "@/components/ui/info-hint";

type SectionCardProps = {
  title: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  contentClassName?: string;
  hint?: string;
};

export function SectionCard({ title, description, action, children, contentClassName, hint }: SectionCardProps) {
  return (
    <Card title={hint} className="group relative rounded-2xl border border-slate-200 bg-white shadow-soft">
      <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <CardTitle className="text-lg font-semibold tracking-tight text-slate-900">{title}</CardTitle>
            {hint ? <InfoHint content={hint} alwaysVisibleOnParentHover /> : null}
          </div>
          {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
        </div>
        {action}
      </CardHeader>
      <CardContent className={contentClassName ?? "p-6"}>{children}</CardContent>
    </Card>
  );
}
