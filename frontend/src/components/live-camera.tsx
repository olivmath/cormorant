"use client";

import { useEffect, useRef, useState } from "react";
import { Room, RoomEvent, Track } from "livekit-client";
import { fetchMobileCalibration, requestLiveKitToken, saveMobileCalibration, type CameraCalibration } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function LiveCamera() {
  const video = useRef<HTMLVideoElement>(null); const [status, setStatus] = useState("Conectando câmera…"); const [calibration, setCalibration] = useState<CameraCalibration | null>(null); const [points, setPoints] = useState<[number, number][]>([]);
  useEffect(() => { fetchMobileCalibration().then(setCalibration).catch(() => {}); const room = new Room(); requestLiveKitToken("viewer").then(async ({ server_url, token }) => { room.on(RoomEvent.TrackSubscribed, (track) => { if (track.kind === Track.Kind.Video && video.current) { track.attach(video.current); setStatus("Ao vivo"); } }); await room.connect(server_url, token); setStatus("Aguardando celular…"); }).catch(() => setStatus("Vídeo indisponível")); return () => room.disconnect(); }, []);
  function click(event: React.MouseEvent<HTMLDivElement>) { const rect = event.currentTarget.getBoundingClientRect(); const point: [number, number] = [(event.clientX - rect.left) / rect.width, (event.clientY - rect.top) / rect.height]; const next = [...points, point].slice(-2); setPoints(next); if (next.length === 2) { const value = { start: next[0], end: next[1] }; saveMobileCalibration(value).then(setCalibration).then(() => { setPoints([]); setStatus("Linha salva"); }).catch(() => setStatus("Não foi possível salvar a linha")); } }
  const line = points.length === 2 ? { start: points[0], end: points[1] } : calibration;
  return <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="font-semibold">Câmera ao vivo</h2><p className="text-sm text-slate-500">{status}</p></div><Button size="sm" variant="outline" onClick={() => { setPoints([]); setCalibration(null); setStatus("Clique em dois pontos para criar a linha"); }}>Calibrar linha</Button></div><div onClick={click} className="relative aspect-video cursor-crosshair bg-slate-950"><video ref={video} autoPlay muted playsInline className="h-full w-full object-contain" />{line && <svg className="pointer-events-none absolute inset-0 h-full w-full"><line x1={`${line.start[0] * 100}%`} y1={`${line.start[1] * 100}%`} x2={`${line.end[0] * 100}%`} y2={`${line.end[1] * 100}%`} stroke="#22c55e" strokeWidth="4" /></svg>}</div></section>;
}
