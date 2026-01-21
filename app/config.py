import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "Character AI Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    # ComfyUI API Configuration
    COMFYUI_BASE_URL: str = Field(
        default="http://172.30.1.94:8000",
        description="ComfyUI server base URL"
    )
    STABLE_DIFFUSION_API_KEY: str | None = None
    
    UPLOAD_DIR: str = "uploads"
    GENERATED_IMAGES_DIR: str = "generated_images"
    MAX_FILE_SIZE_MB: int = 10
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.GENERATED_IMAGES_DIR, exist_ok=True)
