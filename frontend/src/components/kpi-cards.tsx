"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchStats, type Period, type StatsResponse } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const periods: { key: Period; label: string }[] = [
  { key: "today", label: "Hoje" },
  { key: "hour", label: "Última hora" },
  { key: "week", label: "Semana" },
  { key: "month", label: "Mês" },
];

export function KpiCards() {
  const [stats, setStats] = useState<Record<Period, StatsResponse> | null>(null);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      const values = await Promise.all(periods.map(({ key }) => fetchStats(key)));
      setStats(Object.fromEntries(values.map((value, index) => [periods[index].key, value])) as Record<Period, StatsResponse>);
      setError(false);
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void load(), 0);
    const interval = window.setInterval(() => void load(), 10_000);
    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(interval);
    };
  }, [load]);

  if (!stats && error) return <p className="text-sm text-red-700">Não foi possível carregar os indicadores.</p>;

  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Indicadores">
      {periods.map(({ key, label }) => {
        const value = stats?.[key];
        return (
          <Card key={key} className="border border-[#DCE3EC] shadow-none">
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-slate-600">{label}</CardTitle></CardHeader>
            <CardContent className="pt-0">
              {value ? (
                <div className="grid grid-cols-3 divide-x divide-[#DCE3EC]">
                  <Metric label="IN" value={value.count_in} className="text-[#159B64]" />
                  <Metric label="OUT" value={value.count_out} className="pl-3 text-[#E85555]" />
                  <Metric label="Saldo" value={value.net} className="pl-3 text-[#0B1220]" />
                </div>
              ) : <p className="text-sm text-muted-foreground">Carregando indicadores…</p>}
            </CardContent>
          </Card>
        );
      })}
    </section>
  );
}

function Metric({ label, value, className }: { label: string; value: number; className: string }) {
  return <div className={className}><p className="text-[0.7rem] font-medium text-slate-500">{label}</p><p className="mt-1 text-2xl font-semibold tracking-[-0.04em]">{value}</p></div>;
}
