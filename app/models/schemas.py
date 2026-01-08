from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel


@dataclass
class StableDiffusionConfig:
    base_url: str
    api_key: Optional[str]
    default_model: str
    default_sampler: str
    default_steps: int
    default_cfg_scale: float


class TransformRequest(BaseModel):
    style: str = "sd_character"
    denoising_strength: float = 0.42


class TransformResponse(BaseModel):
    success: bool
    original_id: str
    image_id: str
    image_url: str
    original_url: str
    style: str


class HealthResponse(BaseModel):
    status: str
    message: Optional[str] = None
    models_available: Optional[int] = None
    base_url: Optional[str] = None


class GalleryImage(BaseModel):
    id: str
    url: str
    style: str
