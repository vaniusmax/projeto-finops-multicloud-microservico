"use client";

import { useRouter } from "next/navigation";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

type HeaderProps = {
  cloud: string;
  activeTab: "dashboard" | "ai";
  filtersQuery: string;
};

export function Header({ cloud, activeTab, filtersQuery }: HeaderProps) {
  const router = useRouter();

  return (
    <header className="mb-6 border-b border-slate-200 pb-4">
      <h1 className="text-3xl font-bold text-slate-900">PAINEL INTERATIVO - {cloud.toUpperCase()}</h1>
      <Tabs
        value={activeTab}
        className="mt-3"
        onValueChange={(value) => {
          if (value === "dashboard") {
            router.push(`/dashboard?${filtersQuery}`);
            return;
          }
          router.push(`/dashboard?${filtersQuery}&tab=ai`);
        }}
      >
        <TabsList>
          <TabsTrigger value="dashboard">DASHBOARD</TabsTrigger>
          <TabsTrigger value="ai">ASSISTENTE DE IA</TabsTrigger>
        </TabsList>
      </Tabs>
    </header>
  );
}
