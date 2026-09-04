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

  return <section className="flex flex-wrap items-center gap-2" aria-label="Status das câmeras">
    <span className="mr-1 text-sm font-medium">Câmeras</span>
    {error ? <span className="text-sm text-red-700">Não foi possível carregar.</span> : !cameras ? <span className="text-sm text-muted-foreground">Carregando…</span> : cameras.map((camera) => (
      <Badge key={camera.camera_id} className={camera.is_online ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}>
        <span className={`h-1.5 w-1.5 rounded-full ${camera.is_online ? "bg-emerald-600" : "bg-red-600"}`} />{camera.label}
      </Badge>
    ))}
  </section>;
}
