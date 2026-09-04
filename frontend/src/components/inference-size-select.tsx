// chave seletora da resolução de inferência (velocidade vs. precisão)
"use client";

import { useEffect, useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { fetchInferenceSize, saveInferenceSize } from "@/lib/api";

const LABELS: Record<string, string> = {
  full: "Full (640px)",
  medium: "Média (480px)",
  fast: "Rápida (320px)",
};

export function InferenceSizeSelect() {
  const [current, setCurrent] = useState<string | null>(null);
  const [options, setOptions] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchInferenceSize()
      .then((config) => {
        setCurrent(config.size_name);
        setOptions(config.available_sizes);
      })
      .catch(() => {});
  }, []);

  async function handleChange(value: string | null) {
    if (!value) return;
    setSaving(true);
    try {
      const config = await saveInferenceSize(value);
      setCurrent(config.size_name);
    } finally {
      setSaving(false);
    }
  }

  if (!current) return null;

  return (
    <Select value={current} onValueChange={handleChange} disabled={saving}>
      <SelectTrigger className="h-8 w-[190px] bg-white/10 text-white border-white/20 text-sm">
        <SelectValue placeholder="Resolução" />
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
