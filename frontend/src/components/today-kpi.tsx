"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchStats, type StatsResponse } from "@/lib/api";

export function TodayKpi() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      setStats(await fetchStats("today"));
      setError(false);
    } catch {
      setError(true);
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

  if (!stats && error)
    return (
      <p className="text-sm text-red-600">Indicadores indisponíveis.</p>
    );

  if (!stats)
    return (
      <div className="h-[88px] animate-pulse rounded-xl border border-border bg-white" />
    );

  return (
    <section
      className="flex items-center gap-6 rounded-xl border border-border bg-white px-6 py-5 sm:gap-10"
      aria-label="Indicadores de hoje"
    >
      <Stat value={stats.count_in} label="entraram" color="text-entry" />
      <Stat value={stats.count_out} label="saíram" color="text-exit" />
      <div className="border-l border-border pl-6 sm:pl-10">
        <Stat
          value={stats.net}
          label="na loja"
          color="text-night"
          signed
        />
      </div>
    </section>
  );
}

function Stat({
  value,
  label,
  color,
  signed,
}: {
  value: number;
  label: string;
  color: string;
  signed?: boolean;
}) {
  const display = signed && value > 0 ? `+${value}` : String(value);
  return (
    <div>
      <p className={`text-3xl font-semibold tabular-nums tracking-tight sm:text-4xl ${color}`}>
        {display}
      </p>
      <p className="mt-0.5 text-sm text-muted-foreground">{label}</p>
    </div>
  );
}
