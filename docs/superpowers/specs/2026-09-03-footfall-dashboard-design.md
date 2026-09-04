# Footfall Dashboard Design

## Goal

Provide a responsive operations dashboard for a retail footfall counter. It shows camera health, directional counts, and current trends from the FastAPI backend.

## Scope

Create a Next.js App Router frontend in `frontend/`, initialize shadcn/ui, and add `card`, `badge`, and Recharts. Use `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000`.

## Layout

```txt
Camera status
KPI cards: Today | Hour | Week | Month
Hourly line chart
Daily grouped bar chart
```

At desktop widths the dashboard uses multi-column grids; on small screens each section stacks. Cards use concise labels, visible loading states, and a plain error state that preserves page layout.

## API Contract

`src/lib/api.ts` exposes:

```ts
fetchStats(period: "today" | "hour" | "week" | "month"): Promise<StatsResponse>
fetchHourlyTrend(): Promise<TrendResponse>
fetchDailyTrend(): Promise<TrendResponse>
fetchCameras(): Promise<CameraResponse[]>
```

Requests target `${NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api`. The frontend expects stats responses with `count_in`, `count_out`, and `net`; trend responses with `buckets`; and camera responses with `camera_id`, `label`, and `is_online`.

## Components

| Component | Responsibility |
|---|---|
| `KpiCards` | Fetches today/hour/week/month totals on mount and every 10 seconds; displays incoming in green and outgoing in red. |
| `HourlyChart` | Fetches the hourly trend and renders a two-series Recharts `LineChart` in a shadcn Card. |
| `DailyChart` | Fetches the daily trend and renders a grouped Recharts `BarChart` in a shadcn Card. |
| `CameraStatus` | Fetches cameras and renders one status Badge per camera: green online, red offline. |
| `page.tsx` | Arranges the status area, KPI grid, and chart cards responsively. |

All files created for this feature remain under 150 lines.

## Error, Loading, and Refresh Behavior

Components load independently. Before data arrives, they show a compact loading label. If a request fails, they show a direct error message in the affected section; other data remains usable. KPI refresh errors retain the most recently rendered counts.

## Visual Direction

The interface takes its cue from a retail operations console: quiet neutral surfaces, strong count legibility, and color reserved for direction and availability. Green represents entries/online cameras; red represents exits/offline cameras. Charts remain label-led and accessible without relying only on color.

## Testing

Unit tests cover API URL construction and component behavior with mocked fetch responses: the four KPI periods, chart data mapping, camera status colors, loading states, and errors. Tests use the project test runner selected during Next.js setup.
