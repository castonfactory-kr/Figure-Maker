"""
Z-Image API Service for Character Transformation
Using ComfyUI Workflow API (Controlnet Z-image Workflow with WD14 Tagger)
"""

import io
import json
import random
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.config import settings

logger = logging.getLogger(__name__)

# 프로젝트 루트 / preset 이미지 경로
BASE_DIR = Path(__file__).parent.parent.parent
PRESET_DIR = BASE_DIR / "static" / "images" / "preset"


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

# 캐릭터 스타일 설정 (3가지)
# reference_image: Load Image (Reference Image) 노드 19에 입력되는 프리셋 이미지
CHARACTER_STYLES = {
    "real_bubblehead": {
        "name": "리얼 (버블헤드)",
        "name_en": "Real (Bubble Head)",
        "description": "실사풍 큰 머리 캐릭터",
        "prompt": "A high-quality photorealistic portrait. The subject has realistic skin texture and facial features. Clean studio lighting, sharp focus, professional photography quality, pure solid white background.",
        "reference_image": "preset_real_standing.png",
    },
    "semi_realistic": {
        "name": "디즈니 (3D)",
        "name_en": "Disney (3D)",
        "description": "디즈니/픽사 3D 스타일",
        "prompt": "A flawless, ultra-detailed 3D stylized character render reminiscent of high-end Disney and Pixar animations. The subject exhibits smooth 3D proportions and expressive features with subtle subsurface scattering on the skin. Rendered in a clean studio environment using Unreal Engine 5 aesthetic, focusing on smooth and balanced lighting with very soft shadows, vibrant colors, and sharp, clear focus across the entire model. Pure solid white background.",
        "reference_image": "preset_3d_standing.png",
    },
    "character": {
        "name": "치비 (넨도로이드)",
        "name_en": "Chibi (Nendoroid)",
        "description": "넨도로이드 피규어 스타일",
        "prompt": "A precise character design reference of a Nendoroid figure. The subject is constructed from smooth, solid matte plastic. Neutral, flat studio lighting to entirely eliminate harsh shadows and extreme highlights. Clear structural details, distinct facial features, orthographic-style presentation, pure solid white background, perfect for clean feature extraction and 3D miniature aesthetic.",
        "reference_image": "preset_nendo_standing.jpg",
    },
}


class ZImageService:
    """Z-Image API 서비스 (via ComfyUI Workflow with WD14 Tagger)"""

    def __init__(self):
        self.base_url = settings.ZIMAGE_BASE_URL.rstrip("/")
        self.timeout = 180.0
        self.client_id = str(uuid.uuid4())

    def _get_workflow_template(
        self,
        user_image_filename: str,
        reference_image_filename: str,
        positive_prompt_preset: str,
        seed: Optional[int] = None
    ) -> dict:
        """
        ComfyUI Z-Image 워크플로우 생성 (Controlnet Z-image Workflow 기반)

        노드 구조:
        - Node 1: UNETLoader (z_image_turbo_bf16)
        - Node 2: CLIPLoader (qwen_3_4b, lumina2)
        - Node 3: ModelSamplingAuraFlow (shift=3)
        - Node 4: VAELoader (ae.safetensors)
        - Node 5: ImageScaleToTotalPixels (1.5MP, WD14 입력용)
        - Node 7: VAEDecode
        - Node 8: CLIPTextEncode (negative)
        - Node 9: SaveImage
        - Node 10: KSampler (steps=8, cfg=7, euler, simple, denoise=0.75)
        - Node 11: LoadImage (User Input)
        - Node 12: CLIPTextEncode (positive, WD14 tags + preset prompt)
        - Node 15: ModelPatchLoader (Controlnet)
        - Node 16: QwenImageDiffsynthControlnet
        - Node 19: LoadImage (Reference Image = preset)
        - Node 20: WD14Tagger|pysssss (auto-tagging)
        - Node 21: PrimitiveString (preset style prompt)
        - Node 22: Text Concatenate (preset + WD14 tags)
        - Node 23: EmptyLatentImage (712x1072)
        """
        if seed is None:
            seed = 20260112  # 🍀 행운의 시드

        return {
            # UNETLoader (Node 1)
            "1": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": "z_image_turbo_bf16.safetensors",
                    "weight_dtype": "default"
                }
            },
            # CLIPLoader (Node 2)
            "2": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": "qwen_3_4b.safetensors",
                    "type": "lumina2",
                    "device": "default"
                }
            },
            # ModelSamplingAuraFlow (Node 3)
            "3": {
                "class_type": "ModelSamplingAuraFlow",
                "inputs": {
                    "model": ["16", 0],
                    "shift": 3.0
                }
            },
            # VAELoader (Node 4)
            "4": {
                "class_type": "VAELoader",
                "inputs": {
                    "vae_name": "ae.safetensors"
                }
            },
            # ImageScaleToTotalPixels (Node 5) - WD14 Tagger 입력용
            "5": {
                "class_type": "ImageScaleToTotalPixels",
                "inputs": {
                    "image": ["11", 0],
                    "upscale_method": "nearest-exact",
                    "megapixels": 1.5,
                    "resolution_steps": 1
                }
            },
            # VAEDecode (Node 7)
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["10", 0],
                    "vae": ["4", 0]
                }
            },
            # CLIPTextEncode - Negative (Node 8)
            "8": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["2", 0],
                    "text": NEGATIVE_PROMPT_BASE
                }
            },
            # SaveImage (Node 9)
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["7", 0],
                    "filename_prefix": "zimage_"
                }
            },
            # KSampler (Node 10) - 하이퍼파라미터 변경 금지
            "10": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["3", 0],
                    "positive": ["12", 0],
                    "negative": ["8", 0],
                    "latent_image": ["23", 0],
                    "seed": seed,
                    "steps": 8,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 0.75
                }
            },
            # LoadImage - User Input (Node 11)
            "11": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": user_image_filename
                },
                "_meta": {"title": "Load Image (User Input)"}
            },
            # CLIPTextEncode - Positive (Node 12) - WD14 Tags + Preset Prompt
            "12": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["2", 0],
                    "text": ["22", 0]
                }
            },
            # ModelPatchLoader (Node 15)
            "15": {
                "class_type": "ModelPatchLoader",
                "inputs": {
                    "name": "Z-Image-Turbo-Fun-Controlnet-Union.safetensors"
                }
            },
            # QwenImageDiffsynthControlnet (Node 16)
            "16": {
                "class_type": "QwenImageDiffsynthControlnet",
                "inputs": {
                    "model": ["1", 0],
                    "model_patch": ["15", 0],
                    "vae": ["4", 0],
                    "image": ["19", 0],
                    "strength": 0.9
                }
            },
            # LoadImage - Reference Image / Preset (Node 19)
            "19": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": reference_image_filename
                },
                "_meta": {"title": "Load Image (Reference Image)"}
            },
            # WD14Tagger (Node 20) - 자동 태깅
            "20": {
                "class_type": "WD14Tagger|pysssss",
                "inputs": {
                    "image": ["5", 0],
                    "model": "wd-v1-4-moat-tagger-v2",
                    "threshold": 0.25,
                    "character_threshold": 0.8,
                    "replace_underscore": False,
                    "trailing_comma": False,
                    "exclude_tags": "grey background, simple background, white background, black background, closed eyes, winking, blinking, one eye closed, asleep"
                }
            },
            # PrimitiveString - Preset Style Prompt (Node 21)
            "21": {
                "class_type": "PrimitiveString",
                "inputs": {
                    "value": positive_prompt_preset
                }
            },
            # Text Concatenate (Node 22) - Preset Prompt + WD14 Tags
            "22": {
                "class_type": "Text Concatenate",
                "inputs": {
                    "text_a": ["21", 0],  # Preset Style Prompt 
                    "text_b": ["20", 0],  # WD14 Tags
                    "delimiter": ", ",
                    "clean_whitespace": "true"
                }
            },
            # EmptyLatentImage (Node 23)
            "23": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 712,
                    "height": 1072,
                    "batch_size": 1
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

    async def _upload_preset_image(self, preset_filename: str) -> str:
        """프리셋 레퍼런스 이미지를 ComfyUI에 업로드"""
        preset_path = PRESET_DIR / preset_filename
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset image not found: {preset_path}")
        
        image_bytes = preset_path.read_bytes()
        return await self.upload_image(image_bytes, preset_filename)

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
    ) -> bytes:
        """이미지를 캐릭터로 변환 (ComfyUI Z-Image with WD14 Tagger)"""

        style_config = CHARACTER_STYLES.get(style, CHARACTER_STYLES["real_bubblehead"])

        # 1. 사용자 이미지 업로드 (User Input - Node 11)
        user_filename = f"upload_{uuid.uuid4().hex}.png"
        uploaded_user_filename = await self.upload_image(image_bytes, user_filename)
        logger.info(f"User image uploaded: {uploaded_user_filename}")
        
        # 2. 프리셋 레퍼런스 이미지 업로드 (Reference Image - Node 19)
        preset_filename = style_config["reference_image"]
        uploaded_ref_filename = await self._upload_preset_image(preset_filename)
        logger.info(f"Reference image uploaded: {uploaded_ref_filename}")
        
        # 3. Workflow 생성 (Controlnet Z-image Workflow with WD14 Tagger)
        workflow = self._get_workflow_template(
            user_image_filename=uploaded_user_filename,
            reference_image_filename=uploaded_ref_filename,
            positive_prompt_preset=style_config["prompt"],
        )
        
        # 4. Prompt 큐에 추가
        prompt_request = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"Submitting workflow to ComfyUI (style={style})")
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
            
            logger.info(f"Prompt queued: {prompt_id}")
            
            # 5. 결과 대기 및 가져오기
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
                    
                    # 에러 확인
                    status = prompt_history.get("status", {})
                    if status.get("status_str") == "error":
                        messages = status.get("messages", [])
                        error_detail = json.dumps(messages, ensure_ascii=False) if messages else "Unknown error"
                        raise Exception(f"ComfyUI execution error: {error_detail}")
                    
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
                                
                                logger.info(f"Image generated: {filename}")
                                
                                # 이미지 다운로드
                                return await self._download_image(
                                    filename, subfolder, folder_type, client
                                )
            
            if attempt % 10 == 0 and attempt > 0:
                logger.info(f"Waiting for ComfyUI... ({attempt}s elapsed)")
        
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
