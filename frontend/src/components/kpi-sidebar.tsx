"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchStats, type Period, type StatsResponse } from "@/lib/api";

const periods: { key: Period; label: string }[] = [
  { key: "hour", label: "Última hora" },
  { key: "week", label: "Semana" },
  { key: "month", label: "Mês" },
];

export function KpiSidebar() {
  const [stats, setStats] = useState<Record<string, StatsResponse> | null>(
    null,
  );

  const load = useCallback(async () => {
    try {
      const values = await Promise.all(
        periods.map(({ key }) => fetchStats(key)),
      );
      setStats(
        Object.fromEntries(
          values.map((v, i) => [periods[i].key, v]),
        ) as Record<string, StatsResponse>,
      );
    } catch {
      /* silent — sidebar is secondary */
    }
  }, []);

  useEffect(() => {
    const t = window.setTimeout(() => void load(), 0);
    const i = window.setInterval(() => void load(), 10_000);
    return () => {
      window.clearTimeout(t);
      window.clearInterval(i);
    };
  }, [load]);

  return (
    <aside className="flex flex-row gap-3 lg:flex-col" aria-label="Outros períodos">
      {periods.map(({ key, label }) => {
        const v = stats?.[key];
        return (
          <div
            key={key}
            className="flex-1 rounded-xl border border-border bg-white px-4 py-3"
          >
            <p className="mb-2 text-xs font-medium text-muted-foreground">
              {label}
            </p>
            {v ? (
              <div className="flex items-baseline gap-3">
                <span className="text-lg font-semibold tabular-nums text-entry">
                  {v.count_in}
                </span>
                <span className="text-[0.65rem] text-muted-foreground">IN</span>
                <span className="text-lg font-semibold tabular-nums text-exit">
                  {v.count_out}
                </span>
                <span className="text-[0.65rem] text-muted-foreground">OUT</span>
                <span className="ml-auto text-sm font-medium tabular-nums text-night">
                  {v.net > 0 ? `+${v.net}` : v.net}
                </span>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">…</p>
            )}
          </div>
        );
      })}
    </aside>
  );
}
