"use client";

import { useState } from "react";
import { Info } from "lucide-react";

type InfoHintProps = {
  content: string;
  tone?: "default" | "inverse";
  alwaysVisibleOnParentHover?: boolean;
};

export function InfoHint({ content, tone = "default" }: InfoHintProps) {
  const [open, setOpen] = useState(false);

  const iconColor =
    tone === "inverse" ? "text-emerald-50/80 hover:text-white" : "text-slate-400 hover:text-slate-600";

  const tooltipBg =
    tone === "inverse"
      ? "border-emerald-200/20 bg-slate-950 text-white"
      : "border-slate-200 bg-white text-slate-700 shadow-xl";

  return (
    <span
      className="relative inline-flex items-center"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        aria-label="Explicação do card"
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className={`inline-flex h-5 w-5 items-center justify-center rounded-full transition ${iconColor}`}
      >
        <Info className="h-3.5 w-3.5" />
      </button>

      {open ? (
        <span
          role="tooltip"
          className={`absolute right-0 top-full z-[9999] mt-2 w-64 rounded-2xl border px-3 py-2 text-xs font-medium leading-5 ${tooltipBg}`}
        >
          {content}
        </span>
      ) : null}
    </span>
  );
}
