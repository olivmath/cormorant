# Operations Dashboard Design

## Goal

Turn Cormorant into a clear retail operations console: an operator can confirm camera health, see the live entry line, understand entries and exits at a glance, and calibrate the camera without navigating away.

## Design Direction

The dashboard is a calm, high-contrast control surface rather than a collection of generic cards. Live video is the primary operational object; KPIs support it by making the current flow legible within seconds.

## Visual System

| Token | Value | Use |
| --- | --- | --- |
| Night | `#0B1220` | Header, video surround, primary text. |
| Surface | `#F6F8FB` | Page background. |
| Panel | `#FFFFFF` | Cards and active controls. |
| Entry | `#19C37D` | IN labels, entry values, online state. |
| Exit | `#FF6B6B` | OUT labels and exit values. |
| Attention | `#F4B740` | Setup and waiting states. |
| Border | `#DCE3EC` | Structural separation. |

Geist remains the only typeface. Values use compact, large numerals; labels use sentence case and plain operational language.

## Layout

```text
Header: product, location, camera health
KPI strip: Today, last hour, week, month
Main: live camera and calibration controls
Secondary: hourly and daily movement charts
```

At desktop widths, the live camera occupies the main visual column. At smaller widths, content becomes a single vertical operational flow: health, KPIs, camera, charts.

## Components

| Component | Change |
| --- | --- |
| Header | Adds a concise product/location identity and a visible live/offline indicator. |
| KPI cards | Emphasizes net movement and directional totals using color as a secondary cue. |
| Live camera | Adds a status badge, guided calibration copy, line overlay, IN/OUT labels, and grouped actions. |
| Charts | Uses quieter grids, explicit direction colors, and clear empty/loading/error states. |
| Mobile camera | Presents one focused action with large touch targets and direct connection feedback. |

## Interaction States

| State | User-facing message |
| --- | --- |
| Waiting for mobile | `Aguardando transmissão do celular`. |
| Live | `Câmera ao vivo`. |
| Calibration step one | `Clique no início da linha de contagem`. |
| Calibration step two | `Clique no fim da linha de contagem`. |
| Saved | `Linha de contagem salva`. |
| Video unavailable | `Não foi possível conectar ao vídeo. Verifique o LiveKit.` |

## Accessibility

- Preserve text labels alongside status colors.
- Keep buttons keyboard accessible and visibly focused.
- Maintain readable contrast over the video with solid label backgrounds.
- Use `aria-live` for camera and calibration status changes.

## Out of Scope

- New reporting views, user accounts, dark-mode switching, multi-camera layouts, and changes to the counting algorithm.

## Verification

Manual review after implementation:

1. Open the dashboard on desktop and mobile widths.
2. Confirm camera state, KPI strip, video, and charts remain readable.
3. Calibrate a line using two clicks and invert IN/OUT.
4. Confirm the mobile camera page is usable with one hand.
