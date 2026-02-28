import { Suspense } from "react";

import { BudgetsModule } from "@/components/workspace/BudgetsModule";
import { WorkspacePage } from "@/components/workspace/WorkspacePage";

export default function BudgetsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6F7]" />}>
      <WorkspacePage healthLabel="Budget Tracking">
        <BudgetsModule />
      </WorkspacePage>
    </Suspense>
  );
}
