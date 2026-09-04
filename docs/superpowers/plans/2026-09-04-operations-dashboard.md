# Operations Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the responsive operations dashboard and mobile camera flow defined in the approved design specification.

**Architecture:** Preserve the existing client-side data and LiveKit integrations. Rework the dashboard shell and focused components around a shared operational palette; keep camera calibration state inside `LiveCamera`, while its rendered controls expose clear accessible status feedback.

**Tech Stack:** Next.js App Router, React 19, TypeScript, Tailwind CSS 4, Vitest, Testing Library, Recharts, LiveKit.

**Spec:** `docs/superpowers/specs/2026-09-04-operations-dashboard-design.md`

## Execution Status — 2026-09-04

| Item | Status | Evidence |
| --- | --- | --- |
| Visual system and dashboard shell | Implemented | Global tokens, header, health indicator, KPI strip and charts updated. |
| Live camera and calibration | Implemented | Guided two-click calibration, explicit statuses, IN/OUT overlay and accessible live messages added. |
| Mobile camera | Implemented | Single large primary action and connection feedback added. |
| Automated tests | Skipped by request | No tests were created, changed, or executed after the request. |
| Lint | Passed | `pnpm lint` completes without errors. |
| Typecheck | Blocked by existing tests | Only `tests/api.test.ts` and `tests/kpi-cards.test.tsx` report errors; left unchanged by request. |
| Production build | Blocked by environment | Turbopack cannot bind a port while processing CSS in this environment. |
| Visual review | Pending | Local server starts, but browser automation is unavailable in this environment. |

## Global Constraints

- Geist remains the sole typeface.
- Use the exact design colors: Night `#0B1220`, Surface `#F6F8FB`, Panel `#FFFFFF`, Entry `#19C37D`, Exit `#FF6B6B`, Attention `#F4B740`, Border `#DCE3EC`.
- Preserve the existing counting API and LiveKit interfaces; no changes to the counting algorithm.
- Keep text labels beside status colors, visible keyboard focus, video-label contrast, and `aria-live` updates for camera/calibration status.
- Dashboard collapses to one vertical flow on smaller widths; mobile camera retains one large primary action.
- User-directed exception: do not create, change, or run automated tests for this implementation.

---

### Task 1: Establish dashboard visual primitives and layout

**Files:**
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/camera-status.tsx`

**Interfaces:**
- Consumes: `CameraStatus` without props.
- Produces: desktop header and responsive dashboard layout with a labelled camera-health region.

- [x] **Step 1: Implement the operational shell and visible health label**

```tsx
<header className="... bg-[#0B1220] ...">
  <p>Loja principal</p>
  <CameraStatus />
</header>
```

- [ ] **Step 2: Inspect the responsive shell at desktop and mobile widths** — pending browser access.

### Task 2: Rework KPI and chart states for fast directional scanning

**Files:**
- Modify: `frontend/src/components/kpi-cards.tsx`
- Modify: `frontend/src/components/hourly-chart.tsx`
- Modify: `frontend/src/components/daily-chart.tsx`

**Interfaces:**
- Consumes: the existing `fetchStats`, `fetchHourlyTrend`, and `fetchDailyTrend` response shapes.
- Produces: labelled IN, OUT and net values with the design direction colors; charts retain loading, error and empty states.

- [x] **Step 1: Implement compact KPI cells and quiet chart chrome**

```tsx
<Metric label="IN" value={value.count_in} className="text-[#19C37D]" />
```

- [ ] **Step 2: Inspect loading, error, and empty chart states** — pending browser access.

### Task 3: Make live camera calibration explicit and accessible

**Files:**
- Modify: `frontend/src/components/live-camera.tsx`

**Interfaces:**
- Consumes: `requestLiveKitToken`, `fetchMobileCalibration`, and `saveMobileCalibration`.
- Produces: exact operational status copy, a two-click calibration flow, solid IN/OUT line labels, grouped controls, and `aria-live` status.

- [x] **Step 1: Implement the guided camera state and overlay**

```tsx
<p aria-live="polite">{status}</p>
```

- [ ] **Step 2: Inspect the calibration and live-state feedback manually** — pending browser access.

### Task 4: Focus the mobile publisher interface

**Files:**
- Modify: `frontend/src/components/mobile-camera.tsx`

**Interfaces:**
- Consumes: `requestLiveKitToken("publisher")`.
- Produces: a touch-friendly single-action mobile camera screen with direct connection feedback.

- [x] **Step 1: Implement the mobile operation screen**

```tsx
<Button className="h-14 w-full text-base">Iniciar transmissão</Button>
```

- [ ] **Step 2: Inspect the primary action and connection feedback on a narrow viewport** — pending browser access.

### Task 5: Validate responsive operation and regressions

**Files:**
- Verify: `frontend/src/app/page.tsx`
- Verify: `frontend/src/app/camera/page.tsx`

- [ ] **Step 1: Run build, lint, and typecheck**

Run: `pnpm build && pnpm lint && pnpm exec tsc --noEmit`

- [ ] **Step 2: Review the dashboard at desktop and mobile widths**

Check camera state, KPIs, charts, calibration controls, and the mobile camera action.
