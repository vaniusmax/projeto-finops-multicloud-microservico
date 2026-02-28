import { Suspense } from "react";

import { AnalyticsModule } from "@/components/workspace/AnalyticsModule";
import { WorkspacePage } from "@/components/workspace/WorkspacePage";

export default function AnalyticsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6F7]" />}>
      <WorkspacePage healthLabel="Healthy">
        <AnalyticsModule />
      </WorkspacePage>
    </Suspense>
  );
}
