"use client";

import { useEffect, useRef, useState } from "react";
import { Room } from "livekit-client";

import { Button } from "@/components/ui/button";
import { requestLiveKitToken } from "@/lib/api";

export function MobileCamera() {
  const room = useRef<Room | null>(null);
  const [message, setMessage] = useState("Pronto para iniciar a câmera.");
  const [live, setLive] = useState(false);

  useEffect(() => () => {
    void room.current?.disconnect();
  }, []);

  async function start() {
    try {
      setMessage("Conectando à câmera…");
      const credentials = await requestLiveKitToken("publisher");
      const nextRoom = new Room();
      room.current = nextRoom;
      await nextRoom.connect(credentials.server_url, credentials.token);
      await nextRoom.localParticipant.setCameraEnabled(true, { facingMode: "environment" });
      setLive(true);
      setMessage("Câmera ao vivo. Mantenha esta página aberta.");
    } catch (error) {
      setMessage(error instanceof Error && error.message === "LiveKit is not configured"
        ? "Servidor de vídeo não configurado. Contate o administrador."
        : "Não foi possível iniciar. Verifique a permissão da câmera.");
    }
  }

  function stop() {
    room.current?.disconnect();
    room.current = null;
    setLive(false);
    setMessage("Transmissão encerrada.");
  }

  return (
    <main className="min-h-screen bg-[#0B1220] px-5 py-6 text-white">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-md flex-col justify-between rounded-3xl border border-white/10 bg-white/[0.04] p-6 shadow-2xl">
        <div>
          <div className="flex items-center gap-2 text-sm font-medium text-[#8DF0C4]">
            <span className={`h-2 w-2 rounded-full ${live ? "bg-[#19C37D]" : "bg-[#F4B740]"}`} aria-hidden="true" />
            {live ? "Transmissão ativa" : "Câmera da loja"}
          </div>
          <h1 className="mt-5 text-3xl font-semibold tracking-[-0.04em]">Conecte a câmera traseira</h1>
          <p className="mt-3 max-w-xs text-base leading-6 text-white/70" aria-live="polite">{message}</p>
        </div>
        {live ? (
          <Button onClick={stop} variant="destructive" className="h-14 w-full text-base">Encerrar transmissão</Button>
        ) : (
          <Button onClick={start} className="h-14 w-full bg-[#19C37D] text-[#0B1220] text-base hover:bg-[#42D595]">Iniciar transmissão</Button>
        )}
      </div>
    </main>
  );
}
