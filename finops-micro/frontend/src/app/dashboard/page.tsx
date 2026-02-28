import { Suspense } from "react";

import { AIModule } from "@/components/workspace/AIModule";
import { OverviewModule } from "@/components/workspace/OverviewModule";
import { WorkspacePage } from "@/components/workspace/WorkspacePage";

export default function DashboardPage({
  searchParams,
}: {
  searchParams?: { tab?: string };
}) {
  const tab = searchParams?.tab === "ai" ? "ai" : "dashboard";
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6F7]" />}>
      <WorkspacePage healthLabel={tab === "ai" ? "AI Context Ready" : "Healthy"}>
        {tab === "ai" ? <AIModule /> : <OverviewModule />}
      </WorkspacePage>
    </Suspense>
  );
}
