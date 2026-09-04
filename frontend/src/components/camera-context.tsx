"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

const LiveContext = createContext(false);
const SetLiveContext = createContext<(v: boolean) => void>(() => {});

export const useCameraLive = () => useContext(LiveContext);
export const useSetCameraLive = () => useContext(SetLiveContext);

export function CameraLiveProvider({ children }: { children: ReactNode }) {
  const [live, setLive] = useState(false);
  return (
    <LiveContext value={live}>
      <SetLiveContext value={setLive}>
        {children}
      </SetLiveContext>
    </LiveContext>
  );
}
