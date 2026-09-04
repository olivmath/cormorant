// chave seletora do motor de contagem (custom vs ultralytics.solutions)
"use client";

import { useEffect, useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { fetchCountingEngine, saveCountingEngine } from "@/lib/api";

const LABELS: Record<string, string> = {
  custom: "Engine própria",
  ultralytics: "Ultralytics Solutions",
  centroid: "Centroid Tracker",
  iou_sort: "IOU SORT (leve)",
  polygon: "Zona poligonal",
  dwell: "Dwell debounce",
};

export function CountingEngineSelect() {
  const [current, setCurrent] = useState<string | null>(null);
  const [options, setOptions] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchCountingEngine()
      .then((config) => {
        setCurrent(config.engine);
        setOptions(config.available_engines);
      })
      .catch(() => {});
  }, []);

  async function handleChange(value: string | null) {
    if (!value) return;
    setSaving(true);
    try {
      const config = await saveCountingEngine(value);
      setCurrent(config.engine);
    } finally {
      setSaving(false);
    }
  }

  if (!current) return null;

  return (
    <Select value={current} onValueChange={handleChange} disabled={saving}>
      <SelectTrigger className="h-8 w-[190px] bg-white/10 text-white border-white/20 text-sm">
        <SelectValue placeholder="Engine" />
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
