import { CameraStatus } from "@/components/camera-status";
import { DailyChart } from "@/components/daily-chart";
import { HourlyChart } from "@/components/hourly-chart";
import { KpiCards } from "@/components/kpi-cards";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 text-slate-950 sm:px-8 lg:px-12">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div><h1 className="text-3xl font-semibold tracking-tight">CORMORANT</h1><p className="mt-1 text-sm text-slate-600">Monitoramento de fluxo na loja</p></div>
          <CameraStatus />
        </header>
        <KpiCards />
        <div className="grid gap-6 xl:grid-cols-2"><HourlyChart /><DailyChart /></div>
      </div>
    </main>
  );
}
