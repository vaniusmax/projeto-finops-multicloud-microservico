"use client";

import { AppShell } from "@/components/layout/AppShell";

type WorkspacePageProps = {
  children: React.ReactNode;
  showAdvancedFilters?: boolean;
  healthLabel?: string;
};

export function WorkspacePage({ children, showAdvancedFilters = true, healthLabel }: WorkspacePageProps) {
  return (
    <AppShell showAdvancedFilters={showAdvancedFilters} healthLabel={healthLabel}>
      {children}
    </AppShell>
  );
}
