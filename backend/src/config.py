from pydantic_settings import BaseSettings
from pydantic import BaseModel


class CameraConfig(BaseModel):
    camera_id: int
    index: int
    label: str
    line_start: tuple[int, int] = (320, 400)
    line_end: tuple[int, int] = (960, 400)


class Settings(BaseSettings):
    db_path: str = "footfall.db"
    yolo_model: str = "yolov8s.pt"
    confidence_threshold: float = 0.4
    process_every_n_frames: int = 3
    cors_origins: str = (
        "http://localhost:3000,"
        "https://congenial-fiesta-jqpq7gpqj7v35v99-3000.app.github.dev"
    )
    cameras: list[CameraConfig] = [
        CameraConfig(camera_id=0, index=0, label="Mac Built-in"),
        CameraConfig(camera_id=1, index=1, label="iPhone (Continuity)"),
    ]

    model_config = {"env_prefix": "CORMORANT_"}


settings = Settings()
