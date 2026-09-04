"use client";

import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { fetchHourlyTrend, type TrendBucket } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function HourlyChart() {
  const [data, setData] = useState<TrendBucket[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchHourlyTrend().then(({ buckets }) => setData(buckets)).catch(() => setError(true));
  }, []);

  return <Card className="shadow-sm"><CardHeader><CardTitle>Movimento nas últimas 24 horas</CardTitle></CardHeader><CardContent>
    {error ? <p className="text-sm text-red-700">Não foi possível carregar o gráfico.</p> : !data ? <p className="text-sm text-muted-foreground">Carregando…</p> : (
      <div className="h-72"><ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ left: -20 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="hour" /><YAxis allowDecimals={false} /><Tooltip /><Legend />
        <Line type="monotone" dataKey="count_in" name="Entradas" stroke="#15803d" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="count_out" name="Saídas" stroke="#b91c1c" strokeWidth={2} dot={false} />
      </LineChart></ResponsiveContainer></div>
    )}
  </CardContent></Card>;
}
