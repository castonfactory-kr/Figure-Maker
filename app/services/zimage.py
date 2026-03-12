"""
Z-Image API Service for Character Transformation
Using ComfyUI Workflow API
"""

import io
import json
import random
import uuid
import asyncio
from typing import Optional
import httpx
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


# Z-Image base negative prompt
NEGATIVE_PROMPT_BASE = "nsfw, nude, explicit, worst quality, low quality, normal quality, bad anatomy, bad hands, missing fingers, extra digits, fused fingers, mutated, deformed, ugly, blurry, grainy, jpeg artifacts, watermark, signature, text, logo, username, out of frame, mutated proportions, poorly drawn face, overexposed, underexposed, messy lines, flat color, poorly drawn eyes, big nose, ugly, deformed, disfigured, poor anatomy, poorly drawn hands, feet, face, extra limbs, blurry, low quality, jpeg artifacts, low contrast, watermark, signature, out of frame, cut off"

# 캐릭터 스타일 설정 (3가지) - Z-Image 평문 프롬프트
CHARACTER_STYLES = {
    "real_bubblehead": {
        "name": "리얼 (버블헤드)",
        "name_en": "Real (Bubble Head)",
        "description": "실사풍 큰 머리 캐릭터",
        "prompt": "A high-quality photorealistic portrait with bubble head proportions. The subject has a large, detailed head on a small body, maintaining realistic skin texture and facial features. Clean studio lighting, sharp focus, professional photography quality, solid neutral background.",
        "strength": 0.45,
    },
    "semi_realistic": {
        "name": "디즈니 (3D)",
        "name_en": "Disney (3D)",
        "description": "디즈니/픽사 3D 스타일",
        "prompt": "A flawless, ultra-detailed 3D stylized character render reminiscent of high-end Disney and Pixar animations. The subject exhibits smooth 3D proportions and expressive features with subtle subsurface scattering on the skin. Rendered in a clean studio environment using Unreal Engine 5 aesthetic, focusing on smooth and balanced lighting with very soft shadows, vibrant colors, and sharp, clear focus across the entire model.",
        "strength": 0.55,
    },
    "character": {
        "name": "치비 (넨도로이드)",
        "name_en": "Chibi (Nendoroid)",
        "description": "넨도로이드 피규어 스타일",
        "prompt": "A precise character design reference of a Nendoroid figure. The subject is constructed from smooth, solid matte plastic. Neutral, flat studio lighting to entirely eliminate harsh shadows and extreme highlights. Clear structural details, distinct facial features, orthographic-style presentation, pure solid gray background, perfect for clean feature extraction and 3D miniature aesthetic.",
        "strength": 0.60,
    },
}


class ZImageService:
    """Z-Image API 서비스 (via ComfyUI Workflow)"""

    def __init__(self):
        self.base_url = settings.ZIMAGE_BASE_URL.rstrip("/")
        self.timeout = 180.0
        self.client_id = str(uuid.uuid4())

    def _get_workflow_template(
        self,
        image_filename: str,
        positive_prompt_preset: str,
        strength: float = 0.9,
        seed: Optional[int] = None
    ) -> dict:
        """ComfyUI Z-Image 워크플로우 생성"""
        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        return {
            # CLIPLoader (Node 1)
            "1": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": "qwen_3_4b.safetensors",
                    "type": "lumina2",
                    "device": "default"
                }
            },
            # CLIPTextEncode - Negative (Node 2)
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["1", 0],
                    "text": NEGATIVE_PROMPT_BASE
                }
            },
            # ModelSamplingAuraFlow (Node 4)
            "4": {
                "class_type": "ModelSamplingAuraFlow",
                "inputs": {
                    "model": ["8", 0],
                    "shift": 3.0
                }
            },
            # UNETLoader (Node 5)
            "5": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": "z_image_turbo_bf16.safetensors",
                    "weight_dtype": "default"
                }
            },
            # VAELoader (Node 6)
            "6": {
                "class_type": "VAELoader",
                "inputs": {
                    "vae_name": "ae.safetensors"
                }
            },
            # ModelPatchLoader (Node 7)
            "7": {
                "class_type": "ModelPatchLoader",
                "inputs": {
                    "name": "Z-Image-Turbo-Fun-Controlnet-Union.safetensors"
                }
            },
            # QwenImageDiffsynthControlnet (Node 8)
            "8": {
                "class_type": "QwenImageDiffsynthControlnet",
                "inputs": {
                    "model": ["5", 0],
                    "model_patch": ["7", 0],
                    "vae": ["6", 0],
                    "image": ["19", 0],
                    "strength": strength
                }
            },
            # VAEDecode (Node 9)
            "9": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["15", 0],
                    "vae": ["6", 0]
                }
            },
            # SaveImage (Node 10)
            "10": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["9", 0],
                    "filename_prefix": "zimage_"
                }
            },
            # CLIPTextEncode - Positive (Node 11)
            "11": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["1", 0],
                    "text": positive_prompt_preset
                }
            },
            # KSampler (Node 15)
            "15": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["4", 0],
                    "positive": ["11", 0],
                    "negative": ["2", 0],
                    "latent_image": ["20", 0],
                    "seed": seed,
                    "steps": 8,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 0.85
                }
            },
            # ImageScaleToTotalPixels (Node 16)
            "16": {
                "class_type": "ImageScaleToTotalPixels",
                "inputs": {
                    "image": ["18", 0],
                    "upscale_method": "nearest-exact",
                    "megapixels": settings.ZIMAGE_MEGAPIXELS,
                    "resolution_steps": 1
                }
            },
            # LoadImage - User Input (Node 18)
            "18": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": image_filename
                },
                "_meta": {"title": "Load Image (User Input)"}
            },
            # LoadImage - Reference Image (Node 19)
            "19": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": image_filename
                },
                "_meta": {"title": "Load Image (Reference Image)"}
            },
            # VAEEncode (Node 20)
            "20": {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["16", 0],
                    "vae": ["6", 0]
                }
            }
        }

    async def check_connection(self) -> dict:
        """ComfyUI 서버 연결 확인"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/system_stats")
                if response.status_code == 200:
                    stats = response.json()
                    return {
                        "status": "connected",
                        "server_info": stats,
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
                "message": repr(e),
                "base_url": self.base_url
            }

    async def upload_image(self, image_bytes: bytes, filename: str = "input.png") -> str:
        """ComfyUI에 이미지 업로드"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {
                "image": (filename, image_bytes, "image/png"),
            }
            data = {
                "overwrite": "true"
            }
            
            response = await client.post(
                f"{self.base_url}/upload/image",
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                raise Exception(f"Image upload failed: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("name", filename)

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
        strength: float = None,
    ) -> bytes:
        """이미지를 캐릭터로 변환 (ComfyUI Z-Image)"""

        style_config = CHARACTER_STYLES.get(style, CHARACTER_STYLES["real_bubblehead"])

        if strength is None:
            strength = style_config.get("strength", 0.9)

        # 1. 이미지 업로드
        temp_filename = f"upload_{uuid.uuid4().hex}.png"
        uploaded_filename = await self.upload_image(image_bytes, temp_filename)
        
        # 2. Workflow 생성
        workflow = self._get_workflow_template(
            image_filename=uploaded_filename,
            positive_prompt_preset=style_config["prompt"],
            strength=strength
        )
        
        # 3. Prompt 큐에 추가
        prompt_request = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/prompt",
                json=prompt_request
            )
            
            if response.status_code != 200:
                raise Exception(f"Prompt queue failed: {response.status_code} - {response.text}")
            
            result = response.json()
            prompt_id = result.get("prompt_id")
            
            if not prompt_id:
                raise Exception("No prompt_id returned from ComfyUI")
            
            # 4. 결과 대기 및 가져오기
            return await self._wait_for_result(prompt_id, client)
            
    async def _wait_for_result(self, prompt_id: str, client: httpx.AsyncClient) -> bytes:
        """ComfyUI 작업 완료 대기 및 결과 이미지 가져오기"""
        
        # 최대 180초 대기
        max_attempts = 180
        for attempt in range(max_attempts):
            await asyncio.sleep(1)
            
            # History 확인
            response = await client.get(f"{self.base_url}/history/{prompt_id}")
            
            if response.status_code == 200:
                history = response.json()
                
                if prompt_id in history:
                    prompt_history = history[prompt_id]
                    
                    # 완료 확인
                    if "outputs" in prompt_history:
                        outputs = prompt_history["outputs"]
                        
                        # SaveImage 노드(id: 9)의 결과 찾기
                        if "9" in outputs and "images" in outputs["9"]:
                            images = outputs["9"]["images"]
                            if images:
                                image_info = images[0]
                                filename = image_info["filename"]
                                subfolder = image_info.get("subfolder", "")
                                folder_type = image_info.get("type", "output")
                                
                                # 이미지 다운로드
                                return await self._download_image(
                                    filename, subfolder, folder_type, client
                                )
        
        raise Exception("Timeout waiting for ComfyUI to complete")
    
    async def _download_image(
        self,
        filename: str,
        subfolder: str,
        folder_type: str,
        client: httpx.AsyncClient
    ) -> bytes:
        """ComfyUI에서 생성된 이미지 다운로드"""
        params = {
            "filename": filename,
            "type": folder_type
        }
        if subfolder:
            params["subfolder"] = subfolder
        
        response = await client.get(
            f"{self.base_url}/view",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Image download failed: {response.status_code}")
        
        return response.content

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
        return 0.9


# 서비스 인스턴스
zimage_service = ZImageService()
