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
