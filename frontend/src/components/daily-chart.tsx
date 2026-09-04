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

  return <Card className="border border-[#DCE3EC] shadow-none"><CardHeader><CardTitle>Movimento por dia</CardTitle><p className="text-sm text-slate-500">Últimos 30 dias</p></CardHeader><CardContent>
    {error ? <p className="text-sm text-[#C94242]">Não foi possível carregar o gráfico.</p> : !data ? <p className="text-sm text-muted-foreground">Carregando movimento…</p> : data.length === 0 ? <p className="text-sm text-muted-foreground">Ainda não há movimento registrado.</p> : (
      <div className="h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ left: -20 }}>
        <CartesianGrid stroke="#DCE3EC" strokeDasharray="2 5" vertical={false} /><XAxis dataKey="date" tick={{ fill: "#5B6678", fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis allowDecimals={false} tick={{ fill: "#5B6678", fontSize: 12 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ borderColor: "#DCE3EC", borderRadius: 12 }} /><Legend />
        <Bar dataKey="count_in" name="IN" fill="#19C37D" radius={[4, 4, 0, 0]} />
        <Bar dataKey="count_out" name="OUT" fill="#FF6B6B" radius={[4, 4, 0, 0]} />
      </BarChart></ResponsiveContainer></div>
    )}
  </CardContent></Card>;
}
