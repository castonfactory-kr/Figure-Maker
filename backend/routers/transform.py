import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional

from backend.services.openai_service import transform_to_character, get_available_styles
from backend.services.meshy_service import meshy_service

router = APIRouter(prefix="/api/transform", tags=["transform"])

UPLOAD_DIR = "uploads"
GENERATED_IMAGES_DIR = "generated_images"
GENERATED_MODELS_DIR = "generated_models"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)
os.makedirs(GENERATED_MODELS_DIR, exist_ok=True)


@router.get("/styles")
async def list_styles():
    return {"styles": get_available_styles()}


@router.post("/character")
async def transform_character(
    image: UploadFile = File(...),
    style: str = Form(default="sd_character")
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    image_bytes = await image.read()
    
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be less than 10MB")
    
    try:
        result_bytes = transform_to_character(image_bytes, style)
        
        result_id = str(uuid.uuid4())
        result_filename = f"{result_id}.png"
        result_path = os.path.join(GENERATED_IMAGES_DIR, result_filename)
        
        async with aiofiles.open(result_path, "wb") as f:
            await f.write(result_bytes)
        
        return {
            "success": True,
            "image_id": result_id,
            "image_url": f"/api/transform/image/{result_id}",
            "style": style
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Character transformation failed: {str(e)}")


@router.get("/image/{image_id}")
async def get_generated_image(image_id: str):
    image_path = os.path.join(GENERATED_IMAGES_DIR, f"{image_id}.png")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path, media_type="image/png")


def get_public_base_url() -> str:
    if os.environ.get("BASE_PUBLIC_URL"):
        return os.environ.get("BASE_PUBLIC_URL")
    
    dev_domain = os.environ.get("REPLIT_DEV_DOMAIN")
    if dev_domain:
        return f"https://{dev_domain}"
    
    domains = os.environ.get("REPLIT_DOMAINS")
    if domains:
        primary_domain = domains.split(",")[0].strip()
        return f"https://{primary_domain}"
    
    return None


@router.post("/3d-model")
async def create_3d_model(image_id: str = Form(...)):
    image_path = os.path.join(GENERATED_IMAGES_DIR, f"{image_id}.png")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Source image not found")
    
    base_url = get_public_base_url()
    if not base_url:
        return {
            "status": "error",
            "message": "Public URL not available. Set BASE_PUBLIC_URL environment variable for non-Replit environments."
        }
    
    image_url = f"{base_url}/api/transform/image/{image_id}"
    
    try:
        result = await meshy_service.create_3d_model_from_image(image_url, name=f"character_{image_id}")
        result["image_url_used"] = image_url
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"3D model creation failed: {str(e)}")


@router.get("/3d-model/status/{task_id}")
async def get_3d_model_status(task_id: str):
    try:
        result = await meshy_service.get_task_status(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
