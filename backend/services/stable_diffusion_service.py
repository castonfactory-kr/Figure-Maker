import base64
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from backend.config import settings


def is_connection_error(exception: BaseException) -> bool:
    error_msg = str(exception).lower()
    return (
        "connection" in error_msg
        or "timeout" in error_msg
        or "refused" in error_msg
        or isinstance(exception, (httpx.ConnectError, httpx.TimeoutException))
    )


CHARACTER_STYLES = {
    "sd_character": {
        "name": "SD 캐릭터 (치비)",
        "name_en": "SD Character (Chibi)",
        "prompt": "chibi style, super deformed, big head small body, cute anime character, expressive eyes, kawaii, simple background, high quality, detailed",
        "negative_prompt": "realistic, photo, low quality, blurry, deformed"
    },
    "anime": {
        "name": "애니메이션",
        "name_en": "Anime Style",
        "prompt": "anime style, beautiful anime character, cel shaded, expressive anime eyes, detailed hair, high quality anime art, studio ghibli style",
        "negative_prompt": "realistic, photo, 3d render, low quality, blurry"
    },
    "semi_realistic": {
        "name": "반실사 (Pixar)",
        "name_en": "Semi-Realistic (Pixar)",
        "prompt": "pixar style, 3d rendered character, disney style, semi realistic, stylized, smooth skin, expressive eyes, high quality 3d art",
        "negative_prompt": "photo realistic, uncanny valley, low quality, blurry"
    },
    "pixel_art": {
        "name": "픽셀 아트",
        "name_en": "Pixel Art",
        "prompt": "pixel art style, 16-bit retro game character, sprite art, limited color palette, clean pixels, nostalgic game art",
        "negative_prompt": "realistic, blurry, anti-aliased, smooth"
    },
    "cartoon": {
        "name": "카툰 스타일",
        "name_en": "Cartoon Style",
        "prompt": "cartoon style, bold outlines, vibrant colors, exaggerated features, fun character design, comic book style, high contrast",
        "negative_prompt": "realistic, photo, muted colors, low quality"
    }
}


class StableDiffusionService:
    def __init__(self):
        self.base_url = settings.STABLE_DIFFUSION_BASE_URL.rstrip("/")
        self.api_key = settings.STABLE_DIFFUSION_API_KEY
        self.timeout = 120.0
    
    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def check_connection(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/sdapi/v1/sd-models",
                    headers=self._get_headers()
                )
                if response.status_code == 200:
                    models = response.json()
                    return {
                        "status": "connected",
                        "models_available": len(models),
                        "base_url": self.base_url
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Server returned {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "disconnected",
                "message": str(e),
                "base_url": self.base_url
            }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception(is_connection_error),
        reraise=True
    )
    async def transform_to_character(
        self,
        image_bytes: bytes,
        style: str = "sd_character",
        denoising_strength: float = 0.7
    ) -> bytes:
        style_config = CHARACTER_STYLES.get(style, CHARACTER_STYLES["sd_character"])
        
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        payload = {
            "init_images": [image_base64],
            "prompt": f"portrait of a person transformed into {style_config['prompt']}, masterpiece, best quality",
            "negative_prompt": style_config["negative_prompt"],
            "sampler_name": settings.SD_DEFAULT_SAMPLER,
            "steps": settings.SD_DEFAULT_STEPS,
            "cfg_scale": settings.SD_DEFAULT_CFG_SCALE,
            "denoising_strength": denoising_strength,
            "width": 512,
            "height": 512,
            "seed": -1,
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/sdapi/v1/img2img",
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Stable Diffusion API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if "images" not in result or len(result["images"]) == 0:
                raise Exception("No image returned from Stable Diffusion API")
            
            result_base64 = result["images"][0]
            return base64.b64decode(result_base64)
    
    def get_available_styles(self) -> dict:
        return {k: {"name": v["name"], "name_en": v["name_en"]} for k, v in CHARACTER_STYLES.items()}


sd_service = StableDiffusionService()
