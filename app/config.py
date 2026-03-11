import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "Cast on factory AI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    # Z-Image API Configuration
    ZIMAGE_BASE_URL: str = Field(
        default="http://172.30.1.94:8088",
        description="Z-Image server base URL"
    )
    ZIMAGE_MEGAPIXELS: float = Field(
        default=1.0,
        description="Output image megapixels for Z-Image"
    )
    
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
