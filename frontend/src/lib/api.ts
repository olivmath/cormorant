export type Period = "today" | "hour" | "week" | "month";

export type StatsResponse = {
  period: string;
  count_in: number;
  count_out: number;
  net: number;
  from_time: string;
  to_time: string;
};

export type TrendBucket = {
  hour?: string;
  date?: string;
  count_in: number;
  count_out: number;
};

export type TrendResponse = { buckets: TrendBucket[] };

export type CameraResponse = {
  camera_id: number;
  label: string;
  is_online: boolean;
  last_seen: string | null;
};

export type LiveKitCredentials = { server_url: string; token: string; room: string };
export type CameraCalibration = { start: [number, number]; end: [number, number] };

const baseUrl = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${baseUrl()}/api${path}`);
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const fetchStats = (period: Period) =>
  get<StatsResponse>(`/stats?period=${period}`);

export const fetchHourlyTrend = () => get<TrendResponse>("/stats/hourly");

export const fetchDailyTrend = () => get<TrendResponse>("/stats/daily");

export const fetchCameras = () => get<CameraResponse[]>("/cameras");

export async function requestLiveKitToken(role: "publisher" | "viewer"): Promise<LiveKitCredentials> {
  const response = await fetch(`${baseUrl()}/api/livekit/token`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ role }) });
  if (!response.ok) {
    let detail = `Live video is unavailable (${response.status})`;
    try {
      const body = await response.json() as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
    }
    throw new Error(detail);
  }
  return response.json() as Promise<LiveKitCredentials>;
}

export type DetectorConfig = { model_name: string; available_models: string[] };

export const fetchDetector = () => get<DetectorConfig>("/detector");
export async function saveDetector(model_name: string) {
  const response = await fetch(`${baseUrl()}/api/detector`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model_name }) });
  if (!response.ok) throw new Error("Could not save detector model");
  return response.json() as Promise<DetectorConfig>;
}

export const fetchMobileCalibration = () => get<CameraCalibration | null>("/cameras/mobile/calibration");
export async function saveMobileCalibration(calibration: CameraCalibration) {
  const response = await fetch(`${baseUrl()}/api/cameras/mobile/calibration`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(calibration) });
  if (!response.ok) throw new Error("Could not save calibration");
  return response.json() as Promise<CameraCalibration>;
}
