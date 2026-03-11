from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel


@dataclass
class ZImageConfig:
    base_url: str
    default_strength: float
    default_steps: int
    default_guidance_scale: float
    default_megapixels: float


class TransformRequest(BaseModel):
    style: str = "real_bubblehead"
    strength: float = 0.5


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
    base_url: Optional[str] = None


class GalleryImage(BaseModel):
    id: str
    url: str
    style: str
