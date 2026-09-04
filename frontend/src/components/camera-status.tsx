"use client";

import { useEffect, useState } from "react";

import { fetchCameras, type CameraResponse } from "@/lib/api";
import { useCameraLive } from "@/components/camera-context";

export function CameraStatus() {
  const [cameras, setCameras] = useState<CameraResponse[] | null>(null);
  const [error, setError] = useState(false);
  const liveKitConnected = useCameraLive();

  useEffect(() => {
    fetchCameras().then(setCameras).catch(() => setError(true));
  }, []);

  const apiOnline = cameras?.some((c) => c.is_online);
  const online = liveKitConnected || apiOnline;

  return (
    <div className="flex items-center gap-2" aria-label="Status da câmera" aria-live="polite">
      {error && !liveKitConnected ? (
        <span className="text-xs text-red-300">Câmera indisponível</span>
      ) : !cameras && !liveKitConnected ? (
        <span className="text-xs text-white/50">Verificando…</span>
      ) : (
        <>
          <span
            className={`h-1.5 w-1.5 rounded-full ${online ? "bg-entry" : "bg-exit"}`}
            aria-hidden="true"
          />
          <span className="text-xs text-white/80">
            {online ? "Online" : "Offline"}
          </span>
        </>
      )}
    </div>
  );
}
