import base64
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.config import settings


def is_connection_error(exception: BaseException) -> bool:
    error_msg = str(exception).lower()
    return (
        "connection" in error_msg
        or "timeout" in error_msg
        or "refused" in error_msg
        or isinstance(exception, (httpx.ConnectError, httpx.TimeoutException))
    )


NEGATIVE_PROMPT_BASE = "signature,poor body structure,low-quality drawing,incorrect size,outside the edges,unclear,dull background,logo,cropped,trimmed,body parts separated,uneven size,twisted,copy,duplicated elements,additional arms,additional fingers,additional hands,additional legs,additional body parts,flaw,imperfection,joined fingers,unpleasant size,identifying sign,incorrect structure,wrong proportion,tacky,poor quality,poor clarity,spot,absent arms,absent fingers,absent hands,absent legs,error,damaged,beyond the image,badly drawn face,badly drawn feet,badly drawn hands,text on paper,repulsive,narrow eyes,visual plan,arrangement,cut off,unpleasant,blurry,unattractive,awkward position,imaginary framework,watermark,worst quality,low contrast,username,text,bad anatomy,bad hands,missing fingers,extra digit,fewer digits,jpeg artifacts,bad feet,extra fingers,mutated hands,poorly drawn hands,bad proportions,extra limbs,disfigured,gross proportions,malformed limbs,missing arms,missing legs,extra arms,extra legs,fused fingers,too many fingers,long neck,sign,underwear,sexy,lewd,nsfw,exhibitionism,no body,no legs,no hands,missing body parts,un human,monster,amputee,unrealistic items"

CHARACTER_STYLES = {
    "real_bubblehead": {
        "name": "리얼 (버블헤드)",
        "name_en": "Real (Bubble Head)",
        "description": "실사풍 큰 머리 캐릭터",
        "prompt": "full figure,from head to feet,full body,posing,bubble head,big head small body,realistic skin texture,photorealistic style,cute proportions,well-tailored,high definition,4k,high quality"
    },
    "semi_realistic": {
        "name": "반실사 (3D)",
        "name_en": "Semi-Realistic (3D)",
        "description": "3D 애니메이션 스타일",
        "prompt": "full figure,from head to feet,full body,posing,3d rendered character,semi realistic,stylized,smooth skin,expressive eyes,pixar style,high quality 3d art,well-tailored,high definition,4k,high quality"
    },
    "character": {
        "name": "캐릭터",
        "name_en": "Character",
        "description": "동화풍 캐릭터 스타일",
        "prompt": "full figure,from head to feet,full body,posing,fairy tale style,magical character,enchanting,storybook illustration,whimsical,expressive eyes,vibrant colors,well-tailored,high definition,4k,high quality"
    },
    "anime": {
        "name": "애니메이션",
        "name_en": "Anime Style",
        "description": "일본 애니메이션 스타일",
        "prompt": "full figure,from head to feet,full body,posing,anime style,beautiful anime character,cel shaded,expressive anime eyes,detailed hair,high quality anime art,well-tailored,high definition,4k,high quality"
    }
}

RECOMMENDED_DENOISING_STRENGTH = 0.32


class StableDiffusionService:
    def __init__(self):
        self.base_url = settings.STABLE_DIFFUSION_BASE_URL.rstrip("/")
        self.api_key = settings.STABLE_DIFFUSION_API_KEY
        self.timeout = 180.0
    
    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            if ":" in self.api_key:
                credentials = base64.b64encode(self.api_key.encode()).decode()
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
        style: str = "real_bubblehead",
        denoising_strength: float = RECOMMENDED_DENOISING_STRENGTH
    ) -> bytes:
        style_config = CHARACTER_STYLES.get(style, CHARACTER_STYLES["real_bubblehead"])
        
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
