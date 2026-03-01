import { Suspense } from "react";

import { WeeklyDetailModule } from "@/components/workspace/WeeklyDetailModule";
import { WorkspacePage } from "@/components/workspace/WorkspacePage";

export default function WeeklyPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6F7]" />}>
      <WorkspacePage healthLabel="Weekly Deep Dive">
        <WeeklyDetailModule />
      </WorkspacePage>
    </Suspense>
  );
}
