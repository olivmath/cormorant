import Link from "next/link";
import { CameraLiveProvider } from "@/components/camera-context";
import { CameraStatus } from "@/components/camera-status";
import { DailyChart } from "@/components/daily-chart";
import { HourlyChart } from "@/components/hourly-chart";
import { KpiSidebar } from "@/components/kpi-sidebar";
import { LiveCamera } from "@/components/live-camera";
import { TodayKpi } from "@/components/today-kpi";

export default function Home() {
  return (
    <CameraLiveProvider>
      <main className="min-h-screen bg-surface px-4 py-4 text-night sm:px-6 sm:py-6 lg:px-8">
        <div className="mx-auto max-w-7xl space-y-4">
          <header className="flex items-center justify-between rounded-xl bg-night px-5 py-3 text-white">
            <div className="flex items-baseline gap-3">
              <h1 className="text-lg font-semibold tracking-tight">CORMORANT</h1>
              <span className="text-sm text-white/60">Loja principal</span>
            </div>
            <div className="flex items-center gap-3">
              <CameraStatus />
              <Link
                href="/camera"
                className="rounded-lg bg-white/10 px-3 py-1.5 text-sm font-medium hover:bg-white/20 transition-colors"
              >
                Câmera
              </Link>
            </div>
          </header>

          <TodayKpi />

          <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
            <LiveCamera />
            <KpiSidebar />
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <HourlyChart />
            <DailyChart />
          </div>
        </div>
      </main>
    </CameraLiveProvider>
  );
}
