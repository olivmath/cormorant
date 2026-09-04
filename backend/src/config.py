from pydantic_settings import BaseSettings
from pydantic import AliasChoices, BaseModel, Field


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
    livekit_url: str = Field(
        default="",
        validation_alias=AliasChoices("CORMORANT_LIVEKIT_URL", "LIVEKIT_URL"),
    )
    livekit_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("CORMORANT_LIVEKIT_API_KEY", "LIVEKIT_API_KEY"),
    )
    livekit_api_secret: str = Field(
        default="",
        validation_alias=AliasChoices("CORMORANT_LIVEKIT_API_SECRET", "LIVEKIT_API_SECRET"),
    )

    model_config = {
        "env_file": ".env",
        "env_prefix": "CORMORANT_",
    }


settings = Settings()
