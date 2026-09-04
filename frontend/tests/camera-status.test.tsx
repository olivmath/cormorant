import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CameraStatus } from "@/components/camera-status";
import { fetchCameras } from "@/lib/api";

vi.mock("@/lib/api", () => ({ fetchCameras: vi.fn() }));

const mockedFetchCameras = vi.mocked(fetchCameras);

afterEach(() => vi.clearAllMocks());

describe("CameraStatus", () => {
  it("renders each camera with its online or offline state", async () => {
    mockedFetchCameras.mockResolvedValue([
      { camera_id: 0, label: "Front door", is_online: true, last_seen: null },
      { camera_id: 1, label: "Stock room", is_online: false, last_seen: null },
    ]);

    render(<CameraStatus />);

    expect(await screen.findByText("Front door")).toBeInTheDocument();
    expect(screen.getByText("Stock room")).toBeInTheDocument();
    expect(screen.getByText("Front door")).toHaveClass(/green|emerald/);
    expect(screen.getByText("Stock room")).toHaveClass(/red/);
  });

  it("shows a loading state before camera health arrives", () => {
    mockedFetchCameras.mockReturnValue(new Promise(() => {}));

    render(<CameraStatus />);

    expect(screen.getByText(/carregando/i)).toBeInTheDocument();
  });

  it("shows a request error", async () => {
    mockedFetchCameras.mockRejectedValue(new Error("Camera service failed"));

    render(<CameraStatus />);

    expect(await screen.findByText(/não foi possível carregar/i)).toBeInTheDocument();
  });
});
