"use client";

import { QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { ToastProvider } from "@/components/ui/toaster";
import { useToast } from "@/hooks/use-toast";

function QueryProvider({ children }: { children: React.ReactNode }) {
  const { pushToast } = useToast();
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onError: (error) => {
            pushToast({
              title: "Erro ao carregar dados",
              description: error instanceof Error ? error.message : "Tente novamente",
              variant: "destructive",
            });
          },
        }),
      }),
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <QueryProvider>{children}</QueryProvider>
    </ToastProvider>
  );
}
