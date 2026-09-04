"use client";

import { useEffect, useRef, useState } from "react";
import { Room, RoomEvent, Track } from "livekit-client";

import {
  fetchMobileCalibration,
  requestLiveKitToken,
  saveMobileCalibration,
  type CameraCalibration,
} from "@/lib/api";
import { Button } from "@/components/ui/button";

export function LiveCamera() {
  const video = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState("Conectando câmera");
  const [calibration, setCalibration] = useState<CameraCalibration | null>(null);
  const [points, setPoints] = useState<[number, number][]>([]);
  const [isCalibrating, setIsCalibrating] = useState(false);

  useEffect(() => {
    void fetchMobileCalibration().then(setCalibration).catch(() => {});

    const room = new Room();
    let hasVideo = false;

    requestLiveKitToken("viewer")
      .then(async ({ server_url, token }) => {
        room.on(RoomEvent.TrackSubscribed, (track) => {
          if (track.kind === Track.Kind.Video && video.current) {
            track.attach(video.current);
            hasVideo = true;
            setStatus("Câmera ao vivo");
          }
        });

        await room.connect(server_url, token);

        if (!hasVideo) setStatus("Aguardando transmissão do celular");
      })
      .catch(() => setStatus("Não foi possível conectar ao vídeo. Verifique o LiveKit."));

    return () => {
      void room.disconnect();
    };
  }, []);

  function startCalibration() {
    setPoints([]);
    setIsCalibrating(true);
    setStatus("Clique no início da linha de contagem");
  }

  function selectPoint(event: React.MouseEvent<HTMLDivElement>) {
    if (!isCalibrating) return;

    const rect = event.currentTarget.getBoundingClientRect();
    const point: [number, number] = [
      (event.clientX - rect.left) / rect.width,
      (event.clientY - rect.top) / rect.height,
    ];
    const next = [...points, point];

    if (next.length === 1) {
      setPoints(next);
      setStatus("Clique no fim da linha de contagem");
      return;
    }

    const value = { start: next[0], end: next[1] };
    setPoints([]);
    setIsCalibrating(false);
    void saveMobileCalibration(value)
      .then(setCalibration)
      .then(() => setStatus("Linha de contagem salva"))
      .catch(() => setStatus("Não foi possível salvar a linha de contagem."));
  }

  function flipDirection() {
    if (!calibration) return;

    const value = { start: calibration.end, end: calibration.start };
    void saveMobileCalibration(value)
      .then(setCalibration)
      .then(() => setStatus("Sentido IN/OUT invertido"))
      .catch(() => setStatus("Não foi possível inverter o sentido da linha."));
  }

  const line = calibration;
  const dx = line ? line.end[0] - line.start[0] : 0;
  const dy = line ? line.end[1] - line.start[1] : 0;
  const length = Math.hypot(dx, dy) || 1;
  const midpoint = line
    ? [(line.start[0] + line.end[0]) / 2, (line.start[1] + line.end[1]) / 2]
    : [0, 0];
  const normal = { x: (-dy / length) * 0.12, y: (dx / length) * 0.12 };

  return (
    <section className="overflow-hidden rounded-2xl border border-[#DCE3EC] bg-white shadow-[0_10px_30px_rgba(11,18,32,0.06)]">
      <div className="flex flex-col gap-4 border-b border-[#DCE3EC] px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#19C37D]" aria-hidden="true" />
            <h2 className="font-semibold tracking-[-0.02em]">Câmera ao vivo</h2>
          </div>
          <p id="camera-status" className="mt-1 text-sm text-slate-600" aria-live="polite">{status}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" disabled={!calibration} onClick={flipDirection}>
            Inverter IN/OUT
          </Button>
          <Button size="sm" onClick={startCalibration}>
            Calibrar linha
          </Button>
        </div>
      </div>
      <div
        onClick={selectPoint}
        className={`relative aspect-video bg-[#0B1220] ${isCalibrating ? "cursor-crosshair" : "cursor-default"}`}
        aria-describedby="camera-status"
      >
        <video ref={video} autoPlay muted playsInline className="h-full w-full object-contain" aria-label="Transmissão ao vivo da câmera" />
        {line && (
          <svg className="pointer-events-none absolute inset-0 h-full w-full" aria-label="Linha de contagem configurada">
            <line x1={`${line.start[0] * 100}%`} y1={`${line.start[1] * 100}%`} x2={`${line.end[0] * 100}%`} y2={`${line.end[1] * 100}%`} stroke="#19C37D" strokeWidth="4" />
            <g transform={`translate(${(midpoint[0] + normal.x) * 100} ${(midpoint[1] + normal.y) * 100})`}>
              <rect x="-18" y="-14" width="36" height="24" rx="5" fill="#19C37D" />
              <text textAnchor="middle" y="3" fill="#0B1220" fontSize="14" fontWeight="700">IN</text>
            </g>
            <g transform={`translate(${(midpoint[0] - normal.x) * 100} ${(midpoint[1] - normal.y) * 100})`}>
              <rect x="-23" y="-14" width="46" height="24" rx="5" fill="#FF6B6B" />
              <text textAnchor="middle" y="3" fill="#0B1220" fontSize="14" fontWeight="700">OUT</text>
            </g>
          </svg>
        )}
      </div>
    </section>
  );
}
