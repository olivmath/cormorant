"use client";

import { useEffect, useRef, useState } from "react";
import { Room } from "livekit-client";
import { Button } from "@/components/ui/button";
import { requestLiveKitToken } from "@/lib/api";

export function MobileCamera() {
  const room = useRef<Room | null>(null); const [message, setMessage] = useState("Pronto para iniciar a câmera."); const [live, setLive] = useState(false);
  useEffect(() => () => { room.current?.disconnect(); }, []);
  async function start() { try { setMessage("Conectando…"); const credentials = await requestLiveKitToken("publisher"); const nextRoom = new Room(); room.current = nextRoom; await nextRoom.connect(credentials.server_url, credentials.token); await nextRoom.localParticipant.setCameraEnabled(true, { facingMode: "environment" }); setLive(true); setMessage("Ao vivo. Mantenha esta página aberta."); } catch (error) { setMessage(error instanceof Error && error.message === "LiveKit is not configured" ? "Servidor de vídeo não configurado. Contate o administrador." : "Não foi possível iniciar. Verifique a permissão da câmera."); } }
  function stop() { room.current?.disconnect(); room.current = null; setLive(false); setMessage("Transmissão encerrada."); }
  return <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 bg-slate-950 p-6 text-white"><div><p className="text-sm font-medium text-emerald-400">CORMORANT</p><h1 className="mt-2 text-3xl font-semibold">Câmera da loja</h1><p className="mt-2 text-slate-300">{message}</p></div>{live ? <Button onClick={stop} variant="destructive">Encerrar transmissão</Button> : <Button onClick={start}>Iniciar transmissão</Button>}</main>;
}
