"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { fetchDailyTrend, type TrendBucket } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DailyChart() {
  const [data, setData] = useState<TrendBucket[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchDailyTrend().then(({ buckets }) => setData(buckets)).catch(() => setError(true));
  }, []);

  return <Card className="shadow-sm"><CardHeader><CardTitle>Movimento nos últimos 30 dias</CardTitle></CardHeader><CardContent>
    {error ? <p className="text-sm text-red-700">Não foi possível carregar o gráfico.</p> : !data ? <p className="text-sm text-muted-foreground">Carregando…</p> : (
      <div className="h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ left: -20 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="date" tick={{ fontSize: 11 }} /><YAxis allowDecimals={false} /><Tooltip /><Legend />
        <Bar dataKey="count_in" name="Entradas" fill="#15803d" radius={[3, 3, 0, 0]} />
        <Bar dataKey="count_out" name="Saídas" fill="#b91c1c" radius={[3, 3, 0, 0]} />
      </BarChart></ResponsiveContainer></div>
    )}
  </CardContent></Card>;
}
