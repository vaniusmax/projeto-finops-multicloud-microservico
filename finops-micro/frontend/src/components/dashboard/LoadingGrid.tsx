"use client";

import { Skeleton } from "@/components/ui/skeleton";

type LoadingGridProps = {
  cards?: number;
};

export function LoadingGrid({ cards = 4 }: LoadingGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: cards }).map((_, index) => (
        <Skeleton key={index} className="h-[148px] rounded-2xl" />
      ))}
    </div>
  );
}
