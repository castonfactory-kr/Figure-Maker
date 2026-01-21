"""
ComfyUI API Service for Character Transformation
Migrated from Stable Diffusion WebUI to ComfyUI
"""

import base64
import io
import json
import random
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


# 네거티브 프롬프트 베이스 (성별 편향 방지 추가)
NEGATIVE_PROMPT_BASE = "signature,poor body structure,low-quality drawing,incorrect size,outside the edges,unclear,dull background,logo,cropped,trimmed,body parts separated,uneven size,twisted,copy,duplicated elements,additional arms,additional fingers,additional hands,additional legs,additional body parts,flaw,imperfection,joined fingers,unpleasant size,identifying sign,incorrect structure,wrong proportion,tacky,poor quality,poor clarity,spot,absent arms,absent fingers,absent hands,absent legs,error,damaged,beyond the image,badly drawn face,badly drawn feet,badly drawn hands,text on paper,repulsive,narrow eyes,visual plan,arrangement,cut off,unpleasant,blurry,unattractive,awkward position,imaginary framework,watermark,worst quality,low contrast,username,text,bad anatomy,bad hands,missing fingers,extra digit,fewer digits,jpeg artifacts,bad feet,extra fingers,mutated hands,poorly drawn hands,bad proportions,extra limbs,disfigured,gross proportions,malformed limbs,missing arms,missing legs,extra arms,extra legs,fused fingers,too many fingers,long neck,sign,underwear,sexy,lewd,nsfw,exhibitionism,no body,no legs,no hands,missing body parts,un human,monster,amputee,unrealistic items,gender change,different gender,changed gender,altered gender,different person,wrong face,different face,face swap"

# 캐릭터 스타일 설정 (3가지) - 성별 중립적 프롬프트 + 스타일별 denoise 강도
CHARACTER_STYLES = {
    "real_bubblehead": {
        "name": "리얼 (버블헤드)",
        "name_en": "Real (Bubble Head)",
        "description": "실사풍 큰 머리 캐릭터",
        "prompt": "full body portrait,bubble head,big head small body,realistic skin texture,photorealistic style,cute proportions,same person,same face,preserve original features,high definition,4k,high quality",
        "denoise": 0.10  # 원본을 최대한 존중
    },
    "semi_realistic": {
        "name": "반실사 (3D)",
        "name_en": "Semi-Realistic (3D)",
        "description": "3D 애니메이션 스타일",
        "prompt": "full body portrait,3d rendered character,semi realistic,stylized,expressive eyes,pixar style,high quality 3d art,same person,same face,preserve original features,high definition,4k,high quality",
        "denoise": 0.20  # 약간만 변형
    },
    "character": {
        "name": "캐릭터",
        "name_en": "Character",
        "description": "동화풍 캐릭터 스타일",
        "prompt": "full body portrait,fairy tale style,magical character,storybook illustration,whimsical,expressive eyes,vibrant colors,same person,same face,preserve original features,high definition,4k,high quality",
        "denoise": 0.30  # 더 자유롭게 변형
    }
}


# 기본 denoise 강도 (스타일별로 다르게 적용됨)
RECOMMENDED_DENOISING_STRENGTH = 0.22  # fallback용


class ComfyUIService:
    """ComfyUI API 서비스"""
    
    def __init__(self):
        self.base_url = settings.COMFYUI_BASE_URL.rstrip("/")
        self.timeout = 180.0
        self.client_id = str(uuid.uuid4())
    
    def _get_workflow_template(
        self,
        image_filename: str,
        positive_prompt: str,
        negative_prompt: str,
        denoise: float = 0.3,
        steps: int = 20,
        cfg: float = 7.0,
        seed: Optional[int] = None
    ) -> dict:
        """ComfyUI workflow 생성"""
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": image_filename,
                    "upload": "image"
                }
            },
            "2": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "dreamshaper_8.safetensors"
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["2", 1],
                    "text": negative_prompt
                }
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["2", 1],
                    "text": positive_prompt
                }
            },
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["12", 0],
                    "vae": ["9", 0]
                }
            },
            "8": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["7", 0],
                    "filename_prefix": "sd1.5_"
                }
            },
            "9": {
                "class_type": "VAELoader",
                "inputs": {
                    "vae_name": "vaeFtMse840000EmaPruned_vaeFtMse840k.safetensors"
                }
            },
            "10": {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["1", 0],  # LoadImage에서 직접 입력 (ImageScale 제거)
                    "vae": ["9", 0]
                }
            },
            "12": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["2", 0],
                    "positive": ["4", 0],
                    "negative": ["3", 0],
                    "latent_image": ["10", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": denoise
                }
            }
            # ImageScale 노드 제거 - 원본 이미지 크기 유지
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
        reraise=True
    )
    async def transform_to_character(
        self,
        image_bytes: bytes,
        style: str = "real_bubblehead",
        denoising_strength: float = None  # None이면 스타일별 기본값 사용
    ) -> bytes:
        """이미지를 캐릭터로 변환 (ComfyUI)"""
        
        # 스타일 설정 가져오기
        style_config = CHARACTER_STYLES.get(style, CHARACTER_STYLES["real_bubblehead"])
        
        # denoising_strength가 지정되지 않았으면 스타일별 기본값 사용
        if denoising_strength is None:
            denoising_strength = style_config.get("denoise", RECOMMENDED_DENOISING_STRENGTH)
        
        # 1. 이미지 업로드
        temp_filename = f"upload_{uuid.uuid4().hex}.png"
        uploaded_filename = await self.upload_image(image_bytes, temp_filename)
        
        # 2. Workflow 생성
        positive_prompt = style_config["prompt"]
        negative_prompt = NEGATIVE_PROMPT_BASE
        
        workflow = self._get_workflow_template(
            image_filename=uploaded_filename,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            denoise=denoising_strength,
            steps=20,
            cfg=7.0
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
        import asyncio
        
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
                        
                        # SaveImage 노드(id: 8)의 결과 찾기
                        if "8" in outputs and "images" in outputs["8"]:
                            images = outputs["8"]["images"]
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
                "description": v["description"]
            }
            for k, v in CHARACTER_STYLES.items()
        }
    
    def get_recommended_strength(self) -> float:
        """권장 denoising 강도"""
        return RECOMMENDED_DENOISING_STRENGTH


# 서비스 인스턴스
sd_service = ComfyUIService()
