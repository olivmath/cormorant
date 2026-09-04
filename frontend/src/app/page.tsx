import { CameraStatus } from "@/components/camera-status";
import { DailyChart } from "@/components/daily-chart";
import { HourlyChart } from "@/components/hourly-chart";
import { KpiCards } from "@/components/kpi-cards";
import { LiveCamera } from "@/components/live-camera";

export default function Home() {
  return (
    <main className="min-h-screen bg-surface px-4 py-4 text-night sm:px-6 sm:py-6 lg:px-10">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="flex flex-col gap-4 rounded-2xl bg-night px-5 py-5 text-white shadow-[0_12px_30px_rgba(11,18,32,0.14)] sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <p className="text-sm font-medium text-white/65">Operação em tempo real</p>
            <div className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <h1 className="text-2xl font-semibold tracking-[-0.03em]">CORMORANT</h1>
              <p className="text-sm text-white/70">Loja principal</p>
            </div>
          </div>
          <CameraStatus />
        </header>
        <KpiCards />
        <LiveCamera />
        <div className="grid gap-6 xl:grid-cols-2"><HourlyChart /><DailyChart /></div>
      </div>
    </main>
  );
}
