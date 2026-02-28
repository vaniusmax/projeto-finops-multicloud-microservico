import { Suspense } from "react";

import { SettingsModule } from "@/components/workspace/SettingsModule";
import { WorkspacePage } from "@/components/workspace/WorkspacePage";

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6F7]" />}>
      <WorkspacePage showAdvancedFilters={false} healthLabel="Workspace Preferences">
        <SettingsModule />
      </WorkspacePage>
    </Suspense>
  );
}
