import os
import uuid
import json
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional

from backend.config import settings
from backend.services.stable_diffusion_service import sd_service

router = APIRouter(prefix="/api/transform", tags=["transform"])

MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}

EXT_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def get_extension_from_mime(mime_type: str) -> str:
    return MIME_TO_EXT.get(mime_type, ".png")


def get_mime_from_extension(ext: str) -> str:
    return EXT_TO_MIME.get(ext.lower(), "image/png")


@router.get("/styles")
async def list_styles():
    return {"styles": sd_service.get_available_styles()}


@router.get("/health")
async def check_sd_connection():
    return await sd_service.check_connection()


@router.post("/character")
async def transform_character(
    image: UploadFile = File(...),
    style: str = Form(default="sd_character"),
    denoising_strength: float = Form(default=0.7)
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="파일은 이미지여야 합니다")
    
    image_bytes = await image.read()
    
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_size:
        raise HTTPException(
            status_code=400, 
            detail=f"이미지 크기는 {settings.MAX_FILE_SIZE_MB}MB 이하여야 합니다"
        )
    
    original_ext = get_extension_from_mime(image.content_type)
    original_id = str(uuid.uuid4())
    original_filename = f"{original_id}{original_ext}"
    original_path = os.path.join(settings.UPLOAD_DIR, original_filename)
    
    async with aiofiles.open(original_path, "wb") as f:
        await f.write(image_bytes)
    
    meta_path = os.path.join(settings.UPLOAD_DIR, f"{original_id}.json")
    async with aiofiles.open(meta_path, "w") as f:
        await f.write(json.dumps({"ext": original_ext, "mime": image.content_type}))
    
    try:
        result_bytes = await sd_service.transform_to_character(
            image_bytes, 
            style=style,
            denoising_strength=denoising_strength
        )
        
        result_id = str(uuid.uuid4())
        result_filename = f"{result_id}.png"
        result_path = os.path.join(settings.GENERATED_IMAGES_DIR, result_filename)
        
        async with aiofiles.open(result_path, "wb") as f:
            await f.write(result_bytes)
        
        return {
            "success": True,
            "original_id": original_id,
            "image_id": result_id,
            "image_url": f"/api/transform/image/{result_id}",
            "original_url": f"/api/transform/original/{original_id}",
            "style": style
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"캐릭터 변환 실패: {str(e)}"
        )


@router.get("/image/{image_id}")
async def get_generated_image(image_id: str):
    image_path = os.path.join(settings.GENERATED_IMAGES_DIR, f"{image_id}.png")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
    return FileResponse(image_path, media_type="image/png")


@router.get("/original/{image_id}")
async def get_original_image(image_id: str):
    meta_path = os.path.join(settings.UPLOAD_DIR, f"{image_id}.json")
    
    ext = ".png"
    mime_type = "image/png"
    
    if os.path.exists(meta_path):
        try:
            async with aiofiles.open(meta_path, "r") as f:
                meta = json.loads(await f.read())
                ext = meta.get("ext", ".png")
                mime_type = meta.get("mime", "image/png")
        except Exception:
            pass
    
    image_path = os.path.join(settings.UPLOAD_DIR, f"{image_id}{ext}")
    
    if not os.path.exists(image_path):
        for possible_ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            possible_path = os.path.join(settings.UPLOAD_DIR, f"{image_id}{possible_ext}")
            if os.path.exists(possible_path):
                image_path = possible_path
                mime_type = get_mime_from_extension(possible_ext)
                break
        else:
            raise HTTPException(status_code=404, detail="원본 이미지를 찾을 수 없습니다")
    
    return FileResponse(image_path, media_type=mime_type)
