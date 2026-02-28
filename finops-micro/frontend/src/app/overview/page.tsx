import { Suspense } from "react";

import { OverviewModule } from "@/components/workspace/OverviewModule";
import { WorkspacePage } from "@/components/workspace/WorkspacePage";

export default function OverviewPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6F7]" />}>
      <WorkspacePage healthLabel="Healthy">
        <OverviewModule />
      </WorkspacePage>
    </Suspense>
  );
}
