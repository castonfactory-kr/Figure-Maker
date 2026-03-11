"""
Z-Image API Service for Character Transformation
Migrated from ComfyUI/Stable Diffusion to Z-Image img2img API
"""

import base64
import io
import uuid
from typing import Optional
import httpx
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.config import settings


def is_connection_error(exception: BaseException) -> bool:
    """연결 오류 감지"""
    error_msg = str(exception).lower()
    return (
        "connection" in error_msg
        or "timeout" in error_msg
        or "refused" in error_msg
        or isinstance(exception, (httpx.ConnectError, httpx.TimeoutException))
    )


# 캐릭터 스타일 설정 (3가지) - Z-Image 평문 프롬프트
CHARACTER_STYLES = {
    "real_bubblehead": {
        "name": "리얼 (버블헤드)",
        "name_en": "Real (Bubble Head)",
        "description": "실사풍 큰 머리 캐릭터",
        "prompt": "A high-quality photorealistic portrait with bubble head proportions. The subject has a large, detailed head on a small body, maintaining realistic skin texture and facial features. Clean studio lighting, sharp focus, professional photography quality, solid neutral background.",
        "strength": 0.45,
        "guidance_scale": 7.0,
        "num_inference_steps": 20,
    },
    "semi_realistic": {
        "name": "디즈니 (3D)",
        "name_en": "Disney (3D)",
        "description": "디즈니/픽사 3D 스타일",
        "prompt": "A flawless, ultra-detailed 3D stylized character render reminiscent of high-end Disney and Pixar animations. The subject exhibits smooth 3D proportions and expressive features with subtle subsurface scattering on the skin. Rendered in a clean studio environment using Unreal Engine 5 aesthetic, focusing on smooth and balanced lighting with very soft shadows, vibrant colors, and sharp, clear focus across the entire model.",
        "strength": 0.55,
        "guidance_scale": 7.0,
        "num_inference_steps": 20,
    },
    "character": {
        "name": "치비 (넨도로이드)",
        "name_en": "Chibi (Nendoroid)",
        "description": "넨도로이드 피규어 스타일",
        "prompt": "A precise character design reference of a Nendoroid figure. The subject is constructed from smooth, solid matte plastic. Neutral, flat studio lighting to entirely eliminate harsh shadows and extreme highlights. Clear structural details, distinct facial features, orthographic-style presentation, pure solid gray background, perfect for clean feature extraction and 3D miniature aesthetic.",
        "strength": 0.60,
        "guidance_scale": 7.0,
        "num_inference_steps": 20,
    },
}


class ZImageService:
    """Z-Image img2img API 서비스"""

    def __init__(self):
        self.base_url = settings.ZIMAGE_BASE_URL.rstrip("/")
        self.timeout = 180.0

    async def check_connection(self) -> dict:
        """Z-Image 서버 연결 확인"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Z-Image 서버에 간단한 연결 테스트
                response = await client.get(f"{self.base_url}/docs")
                if response.status_code == 200:
                    return {
                        "status": "connected",
                        "base_url": self.base_url,
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Server returned {response.status_code}",
                    }
        except Exception as e:
            return {
                "status": "disconnected",
                "message": repr(e),
                "base_url": self.base_url,
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception(is_connection_error),
        reraise=True,
    )
    async def transform_to_character(
        self,
        image_bytes: bytes,
        style: str = "real_bubblehead",
        strength: Optional[float] = None,
    ) -> bytes:
        """이미지를 캐릭터로 변환 (Z-Image img2img)"""

        # 스타일 설정 가져오기
        style_config = CHARACTER_STYLES.get(
            style, CHARACTER_STYLES["real_bubblehead"]
        )

        # strength가 지정되지 않았으면 스타일별 기본값 사용
        if strength is None:
            strength = style_config.get("strength", 0.5)

        # Z-Image API: image는 파일 업로드, 나머지는 form data
        files = {
            "image": ("input.jpg", image_bytes, "image/jpeg"),
        }
        form_data = {
            "prompt": style_config["prompt"],
            "strength": str(strength),
            "num_inference_steps": str(style_config.get("num_inference_steps", 20)),
            "guidance_scale": str(style_config.get("guidance_scale", 7.0)),
            "megapixels": str(settings.ZIMAGE_MEGAPIXELS),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/img2img",
                files=files,
                data=form_data,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Z-Image API error: {response.status_code} - {response.text}"
                )

            result = response.json()

            # 응답에서 이미지 데이터 추출 (base64 인코딩된 이미지)
            result_image_b64 = result.get("image") or result.get("images", [None])[0]
            if not result_image_b64:
                raise Exception("No image returned from Z-Image API")

            # data:image/... prefix 제거 (있을 경우)
            if "," in result_image_b64:
                result_image_b64 = result_image_b64.split(",", 1)[1]

            return base64.b64decode(result_image_b64)

    def get_available_styles(self) -> dict:
        """사용 가능한 스타일 목록"""
        return {
            k: {
                "name": v["name"],
                "name_en": v["name_en"],
                "description": v["description"],
            }
            for k, v in CHARACTER_STYLES.items()
        }

    def get_recommended_strength(self) -> float:
        """권장 strength 값"""
        return 0.5


# 서비스 인스턴스
zimage_service = ZImageService()
