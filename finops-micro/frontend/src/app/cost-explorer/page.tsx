import { Suspense } from "react";

import { CostExplorerModule } from "@/components/workspace/CostExplorerModule";
import { WorkspacePage } from "@/components/workspace/WorkspacePage";

export default function CostExplorerPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6F7]" />}>
      <WorkspacePage healthLabel="Healthy">
        <CostExplorerModule />
      </WorkspacePage>
    </Suspense>
  );
}
