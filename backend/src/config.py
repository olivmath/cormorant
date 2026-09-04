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
    cameras: list[CameraConfig] = []
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    model_config = {"env_prefix": "CORMORANT_"}


settings = Settings()
