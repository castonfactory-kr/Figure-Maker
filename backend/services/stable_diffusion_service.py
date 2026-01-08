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


NEGATIVE_PROMPT_BASE = "worst quality,low quality,low contrast,blurry,low quality,medium quality,watermark,username,signature,text,bad anatomy,bad hands,error,missing fingers,extra digit,fewer digits,cropped,jpeg artifacts,bad feet,extra fingers,mutated hands,poorly drawn hands,bad proportions,extra limbs,disfigured,bad anatomy,gross proportions,malformed limbs,missing arms,missing legs,extra arms,extra legs,mutated hands,fused fingers,too many fingers,long neck,sign,blurry,underwear,sexy,lewd,nsfw,exhibitionism,no body,no legs,no hands,missing body parts,unhuman,monster,nohands,amputee,cosplay,unrealistic items"

CHARACTER_STYLES = {
    "sd_character": {
        "name": "SD 캐릭터 (치비)",
        "name_en": "SD Character (Chibi)",
        "description": "귀여운 2등신 캐릭터",
        "prompt": "full figure,from head to feet,full body,posing,cute,chibi,super deformed,big head small body,kawaii,anime,figure,well-tailored,high definition,4k,high quality"
    },
    "semi_realistic": {
        "name": "반실사 (3D)",
        "name_en": "Semi-Realistic (3D)",
        "description": "3D 애니메이션 스타일",
        "prompt": "full figure,from head to feet,full body,posing,3d rendered character,semi realistic,stylized,smooth skin,expressive eyes,high quality 3d art,well-tailored,high definition,4k,high quality"
    },
    "anime": {
        "name": "애니메이션",
        "name_en": "Anime Style",
        "description": "일본 애니메이션 스타일",
        "prompt": "full figure,from head to feet,full body,posing,anime style,beautiful anime character,cel shaded,expressive anime eyes,detailed hair,high quality anime art,well-tailored,high definition,4k,high quality"
    },
    "cartoon": {
        "name": "카툰 스타일",
        "name_en": "Cartoon Style",
        "description": "만화 캐릭터 스타일",
        "prompt": "full figure,from head to feet,full body,posing,cartoon style,bold outlines,vibrant colors,exaggerated features,fun character design,comic book style,high contrast,well-tailored,high definition,4k,high quality"
    }
}

RECOMMENDED_DENOISING_STRENGTH = 0.42


class StableDiffusionService:
    def __init__(self):
        self.base_url = settings.STABLE_DIFFUSION_BASE_URL.rstrip("/")
        self.api_key = settings.STABLE_DIFFUSION_API_KEY
        self.timeout = 180.0
    
    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            if ":" in self.api_key:
                import base64 as b64
                credentials = b64.b64encode(self.api_key.encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
            else:
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
        denoising_strength: float = RECOMMENDED_DENOISING_STRENGTH
    ) -> bytes:
        style_config = CHARACTER_STYLES.get(style, CHARACTER_STYLES["sd_character"])
        
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        payload = {
            "init_images": [image_base64],
            "prompt": style_config["prompt"],
            "negative_prompt": NEGATIVE_PROMPT_BASE,
            "sampler_name": "Euler a",
            "scheduler": "Automatic",
            "steps": 45,
            "cfg_scale": 24,
            "denoising_strength": denoising_strength,
            "width": 896,
            "height": 896,
            "seed": -1,
            "resize_mode": 2,
            "batch_size": 1,
            "n_iter": 1,
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
        return {
            k: {
                "name": v["name"], 
                "name_en": v["name_en"],
                "description": v["description"]
            } 
            for k, v in CHARACTER_STYLES.items()
        }
    
    def get_recommended_strength(self) -> float:
        return RECOMMENDED_DENOISING_STRENGTH


sd_service = StableDiffusionService()
