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
    void load();
    const interval = window.setInterval(() => void load(), 10_000);
    return () => window.clearInterval(interval);
  }, [load]);

  if (!stats && error) return <p className="text-sm text-red-700">Não foi possível carregar os indicadores.</p>;

  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Indicadores">
      {periods.map(({ key, label }) => {
        const value = stats?.[key];
        return (
          <Card key={key} className="shadow-sm">
            <CardHeader><CardTitle>{label}</CardTitle></CardHeader>
            <CardContent>
              {value ? (
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <Metric label="Entradas" value={value.count_in} className="text-emerald-700" />
                  <Metric label="Saídas" value={value.count_out} className="text-red-700" />
                  <Metric label="Saldo" value={value.net} className="text-slate-900" />
                </div>
              ) : <p className="text-sm text-muted-foreground">Carregando…</p>}
            </CardContent>
          </Card>
        );
      })}
    </section>
  );
}

function Metric({ label, value, className }: { label: string; value: number; className: string }) {
  return <div><p className="text-xs text-muted-foreground">{label}</p><p className={`text-xl font-semibold ${className}`}>{value}</p></div>;
}
