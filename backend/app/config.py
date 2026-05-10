from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://facedet:facedet@db:5432/facedetdb"
    JPEG_QUALITY: int = 80
    ROI_COLOR: tuple = (0, 255, 80)
    ROI_THICKNESS: int = 3
    FACE_CONFIDENCE_THRESHOLD: float = 0.5
    MAX_SESSION_ID_LENGTH: int = 64
    MAX_FRAME_BYTES: int = 10 * 1024 * 1024  # 10 MB

settings = Settings()