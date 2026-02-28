import { Suspense } from "react";

import { TrendsModule } from "@/components/workspace/TrendsModule";
import { WorkspacePage } from "@/components/workspace/WorkspacePage";

export default function TrendsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6F7]" />}>
      <WorkspacePage healthLabel="Watching Trends">
        <TrendsModule />
      </WorkspacePage>
    </Suspense>
  );
}
