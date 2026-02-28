import { Suspense } from "react";

import { AIModule } from "@/components/workspace/AIModule";
import { WorkspacePage } from "@/components/workspace/WorkspacePage";

export default function AIPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6F7]" />}>
      <WorkspacePage healthLabel="AI Context Ready">
        <AIModule />
      </WorkspacePage>
    </Suspense>
  );
}
