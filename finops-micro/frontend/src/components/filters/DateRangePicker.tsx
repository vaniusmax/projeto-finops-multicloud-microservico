"use client";

import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

type DateRangePickerProps = {
  from: string;
  to: string;
  onChange: (next: { from: string; to: string }) => void;
};

function parseDate(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function toIso(date: Date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function toDisplay(date: Date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}/${m}/${d}`;
}

function monthDays(viewDate: Date) {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const offset = firstDay.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const days: Array<{ date: Date; outside: boolean }> = [];
  for (let i = 0; i < offset; i += 1) {
    days.push({ date: new Date(year, month, i - offset + 1), outside: true });
  }
  for (let i = 1; i <= daysInMonth; i += 1) {
    days.push({ date: new Date(year, month, i), outside: false });
  }
  while (days.length % 7 !== 0) {
    const idx = days.length - (offset + daysInMonth) + 1;
    days.push({ date: new Date(year, month + 1, idx), outside: true });
  }
  return days;
}

function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

export function DateRangePicker({ from, to, onChange }: DateRangePickerProps) {
  const fromDate = useMemo(() => parseDate(from), [from]);
  const toDate = useMemo(() => parseDate(to), [to]);

  const [open, setOpen] = useState(false);
  const [rangeStart, setRangeStart] = useState<Date>(fromDate);
  const [rangeEnd, setRangeEnd] = useState<Date>(toDate);
  const [anchorDate, setAnchorDate] = useState<Date | null>(null);
  const [viewDate, setViewDate] = useState<Date>(fromDate);

  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setRangeStart(fromDate);
    setRangeEnd(toDate);
  }, [fromDate, toDate]);

  useEffect(() => {
    function onClickOutside(event: MouseEvent) {
      if (!ref.current?.contains(event.target as Node)) {
        setOpen(false);
        setAnchorDate(null);
        setRangeStart(fromDate);
        setRangeEnd(toDate);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [fromDate, toDate]);

  const days = useMemo(() => monthDays(viewDate), [viewDate]);

  function handleSelect(date: Date) {
    if (!anchorDate) {
      setAnchorDate(date);
      setRangeStart(date);
      setRangeEnd(date);
      return;
    }

    const start = date < anchorDate ? date : anchorDate;
    const end = date < anchorDate ? anchorDate : date;
    setRangeStart(start);
    setRangeEnd(end);
    onChange({ from: toIso(start), to: toIso(end) });
    setAnchorDate(null);
    setOpen(false);
  }

  const months = [
    "Janeiro",
    "Fevereiro",
    "Marco",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
  ];
  const baseYear = new Date().getFullYear();
  const years = Array.from({ length: 7 }, (_, i) => baseYear - 3 + i);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        className="flex h-11 w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-800 shadow-sm transition hover:border-emerald-200"
        onClick={() => {
          setOpen((value) => !value);
          setAnchorDate(null);
          setRangeStart(fromDate);
          setRangeEnd(toDate);
        }}
      >
        <span className="inline-flex items-center gap-2">
          <CalendarDays className="h-4 w-4 text-emerald-700" />
          {toDisplay(rangeStart)} - {toDisplay(rangeEnd)}
        </span>
      </button>

      {open ? (
        <div className="absolute left-0 z-50 mt-2 w-[320px] rounded-2xl border border-slate-200 bg-white text-slate-800 shadow-soft">
          <div className="flex items-center justify-between border-b border-slate-200 px-3 py-3 text-xs">
            <button
              type="button"
              className="rounded-lg p-1 text-slate-500 transition hover:bg-slate-100"
              onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <div className="flex items-center gap-2">
              <select
                value={viewDate.getMonth()}
                onChange={(e) => setViewDate(new Date(viewDate.getFullYear(), Number(e.target.value), 1))}
                className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-xs"
              >
                {months.map((month, idx) => (
                  <option key={month} value={idx}>{month}</option>
                ))}
              </select>
              <select
                value={viewDate.getFullYear()}
                onChange={(e) => setViewDate(new Date(Number(e.target.value), viewDate.getMonth(), 1))}
                className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-xs"
              >
                {years.map((year) => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
            <button
              type="button"
              className="rounded-lg p-1 text-slate-500 transition hover:bg-slate-100"
              onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          <div className="grid grid-cols-7 gap-0.5 px-2 pt-2 text-center text-[11px] text-slate-500">
            {[
              "Su",
              "Mo",
              "Tu",
              "We",
              "Th",
              "Fr",
              "Sa",
            ].map((d) => (
              <div key={d} className="py-1">{d}</div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-0.5 px-2 pb-2 text-center text-[12px]">
            {days.map(({ date, outside }) => {
              const selectedStart = isSameDay(date, rangeStart);
              const selectedEnd = isSameDay(date, rangeEnd);
              const inRange = date > rangeStart && date < rangeEnd;
              return (
                <button
                  type="button"
                  key={date.toISOString()}
                  onClick={() => handleSelect(date)}
                  className={`mx-auto my-0.5 h-8 w-8 rounded-full ${
                    selectedStart || selectedEnd
                      ? "bg-emerald-700 text-white"
                      : inRange
                        ? "bg-emerald-50 text-emerald-700"
                        : outside
                          ? "text-slate-300"
                          : "text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  {date.getDate()}
                </button>
              );
            })}
          </div>
          <div className="border-t border-slate-200 px-3 py-3 text-xs text-slate-500">
            Selecione data inicial e final no mesmo calendario.
          </div>
        </div>
      ) : null}
    </div>
  );
}
