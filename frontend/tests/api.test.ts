import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.resetModules();
});

function jsonResponse(payload: unknown) {
  return new Response(JSON.stringify(payload), { status: 200 });
}

describe("dashboard API client", () => {
  it("uses localhost and all documented endpoints by default", async () => {
    const fetchMock = vi.fn(() => jsonResponse({ buckets: [] }));
    vi.stubGlobal("fetch", fetchMock);

    const api = await import("@/lib/api");
    await Promise.all([
      api.fetchStats("today"),
      api.fetchStats("hour"),
      api.fetchStats("week"),
      api.fetchStats("month"),
      api.fetchHourlyTrend(),
      api.fetchDailyTrend(),
      api.fetchCameras(),
    ]);

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      "http://localhost:8000/api/stats?period=today",
      "http://localhost:8000/api/stats?period=hour",
      "http://localhost:8000/api/stats?period=week",
      "http://localhost:8000/api/stats?period=month",
      "http://localhost:8000/api/trends/hourly",
      "http://localhost:8000/api/trends/daily",
      "http://localhost:8000/api/cameras",
    ]);
  });

  it("uses NEXT_PUBLIC_API_URL as the API origin", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://counter.example.test");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ count_in: 0 }));
    vi.stubGlobal("fetch", fetchMock);

    const { fetchStats } = await import("@/lib/api");
    await fetchStats("today");

    expect(fetchMock).toHaveBeenCalledWith(
      "https://counter.example.test/api/stats?period=today",
    );
  });
});
