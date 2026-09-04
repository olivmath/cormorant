"use client";

import { useEffect, useState } from "react";

import { fetchCameras, type CameraResponse } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export function CameraStatus() {
  const [cameras, setCameras] = useState<CameraResponse[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchCameras().then(setCameras).catch(() => setError(true));
  }, []);

  const anyOnline = cameras?.some((camera) => camera.is_online);

  return <section className="flex flex-wrap items-center gap-2" aria-label="Status das câmeras" aria-live="polite">
    {error ? <span className="text-sm text-[#FFB3B3]">Não foi possível carregar o status da câmera.</span> : !cameras ? <span className="text-sm text-white/70">Verificando câmera…</span> : <>
      <Badge className={anyOnline ? "border border-[#19C37D]/30 bg-[#19C37D]/15 text-[#8DF0C4]" : "border border-[#FF6B6B]/30 bg-[#FF6B6B]/15 text-[#FFB3B3]"}>
        <span className={`h-1.5 w-1.5 rounded-full ${anyOnline ? "bg-[#19C37D]" : "bg-[#FF6B6B]"}`} />
        {anyOnline ? "Câmera online" : "Câmera offline"}
      </Badge>
      {cameras.map((camera) => (
        <span key={camera.camera_id} className="text-xs text-white/65">{camera.label}</span>
      ))}
    </>}
  </section>;
}
