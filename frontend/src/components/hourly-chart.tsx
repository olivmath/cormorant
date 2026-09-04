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

  return <Card className="border border-[#DCE3EC] shadow-none"><CardHeader><CardTitle>Movimento por hora</CardTitle><p className="text-sm text-slate-500">Últimas 24 horas</p></CardHeader><CardContent>
    {error ? <p className="text-sm text-[#C94242]">Não foi possível carregar o gráfico.</p> : !data ? <p className="text-sm text-muted-foreground">Carregando movimento…</p> : data.length === 0 ? <p className="text-sm text-muted-foreground">Ainda não há movimento registrado.</p> : (
      <div className="h-72"><ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ left: -20 }}>
        <CartesianGrid stroke="#DCE3EC" strokeDasharray="2 5" vertical={false} /><XAxis dataKey="hour" tick={{ fill: "#5B6678", fontSize: 12 }} axisLine={false} tickLine={false} /><YAxis allowDecimals={false} tick={{ fill: "#5B6678", fontSize: 12 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ borderColor: "#DCE3EC", borderRadius: 12 }} /><Legend />
        <Line type="monotone" dataKey="count_in" name="IN" stroke="#19C37D" strokeWidth={2.5} dot={false} />
        <Line type="monotone" dataKey="count_out" name="OUT" stroke="#FF6B6B" strokeWidth={2.5} dot={false} />
      </LineChart></ResponsiveContainer></div>
    )}
  </CardContent></Card>;
}
