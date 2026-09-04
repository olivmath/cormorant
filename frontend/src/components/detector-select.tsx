// chave seletora do modelo de detecção usado pelas câmeras
"use client";

import { useEffect, useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { fetchDetector, saveDetector } from "@/lib/api";

const LABELS: Record<string, string> = {
  yolov8s: "YOLOv8s (rápido)",
  yolov8l: "YOLOv8l (preciso)",
  rtdetr: "RT-DETR (preciso)",
};

export function DetectorSelect() {
  const [current, setCurrent] = useState<string | null>(null);
  const [options, setOptions] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchDetector()
      .then((config) => {
        setCurrent(config.model_name);
        setOptions(config.available_models);
      })
      .catch(() => {});
  }, []);

  async function handleChange(value: string) {
    setSaving(true);
    try {
      const config = await saveDetector(value);
      setCurrent(config.model_name);
    } finally {
      setSaving(false);
    }
  }

  if (!current) return null;

  return (
    <Select value={current} onValueChange={handleChange} disabled={saving}>
      <SelectTrigger className="h-8 w-[190px] bg-white/10 text-white border-white/20 text-sm">
        <SelectValue placeholder="Modelo" />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option} value={option}>
            {LABELS[option] ?? option}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
