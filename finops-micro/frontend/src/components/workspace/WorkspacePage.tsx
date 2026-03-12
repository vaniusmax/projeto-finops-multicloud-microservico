"use client";

import { AuthGate } from "@/components/auth/AuthGate";
import { AppShell } from "@/components/layout/AppShell";

type WorkspacePageProps = {
  children: React.ReactNode;
  showAdvancedFilters?: boolean;
  healthLabel?: string;
};

export function WorkspacePage({ children, showAdvancedFilters = true, healthLabel }: WorkspacePageProps) {
  return (
    <AuthGate>
      <AppShell showAdvancedFilters={showAdvancedFilters} healthLabel={healthLabel}>
        {children}
      </AppShell>
    </AuthGate>
  );
}
