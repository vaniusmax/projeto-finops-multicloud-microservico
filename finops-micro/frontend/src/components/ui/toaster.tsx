"use client";

import { useEffect, useState } from "react";

import { ToastContext, type ToastItem } from "@/hooks/use-toast";

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  function pushToast(toast: Omit<ToastItem, "id">) {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { ...toast, id }]);
  }

  useEffect(() => {
    if (toasts.length === 0) return;
    const timeout = setTimeout(() => {
      setToasts((prev) => prev.slice(1));
    }, 3800);

    return () => clearTimeout(timeout);
  }, [toasts]);

  return (
    <ToastContext.Provider value={{ pushToast }}>
      {children}
      <div className="fixed right-4 top-4 z-[60] flex w-[320px] flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`rounded-xl border px-4 py-3 text-sm shadow-soft ${
              toast.variant === "destructive"
                ? "border-red-200 bg-red-50 text-red-700"
                : "border-slate-200 bg-white text-slate-800"
            }`}
          >
            <div className="font-semibold">{toast.title}</div>
            {toast.description ? <div className="text-xs opacity-90">{toast.description}</div> : null}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
