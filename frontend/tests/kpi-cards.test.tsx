import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { KpiCards } from "@/components/kpi-cards";
import { fetchStats } from "@/lib/api";

vi.mock("@/lib/api", () => ({ fetchStats: vi.fn() }));

const mockedFetchStats = vi.mocked(fetchStats);

afterEach(() => vi.clearAllMocks());

describe("KpiCards", () => {
  it("renders all period totals after loading", async () => {
    mockedFetchStats.mockImplementation(async (period) => ({
      period,
      count_in: { today: 12, hour: 3, week: 55, month: 230 }[period],
      count_out: { today: 5, hour: 1, week: 21, month: 90 }[period],
      net: { today: 7, hour: 2, week: 34, month: 140 }[period],
    }));

    render(<KpiCards />);

    await waitFor(() => expect(screen.getByText("230")).toBeInTheDocument());
    expect(screen.getAllByText("Entradas")).toHaveLength(4);
    expect(screen.getAllByText("Saídas")).toHaveLength(4);
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("140")).toBeInTheDocument();
  });

  it("shows a loading state before totals arrive", () => {
    mockedFetchStats.mockReturnValue(new Promise(() => {}));

    render(<KpiCards />);

    expect(screen.getByText(/carregando/i)).toBeInTheDocument();
  });

  it("shows an error when the initial KPI request fails", async () => {
    mockedFetchStats.mockRejectedValue(new Error("Backend unavailable"));

    render(<KpiCards />);

    expect(await screen.findByText(/não foi possível carregar/i)).toBeInTheDocument();
  });
});
