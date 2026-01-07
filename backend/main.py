from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.config import settings
from backend.routers import transform

app = FastAPI(
    title=settings.APP_NAME,
    description="AI 기반 인물 사진 캐릭터화 서비스 - Stable Diffusion 연동",
    version=settings.APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transform.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/api/info")
async def api_info():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": {
            "list_styles": "GET /api/transform/styles",
            "transform_character": "POST /api/transform/character",
            "get_image": "GET /api/transform/image/{image_id}",
            "get_original": "GET /api/transform/original/{image_id}",
            "check_sd_health": "GET /api/transform/health"
        },
        "description": "인물 사진을 업로드하여 다양한 스타일의 캐릭터 이미지로 변환하는 서비스입니다.",
        "stable_diffusion": {
            "base_url": settings.STABLE_DIFFUSION_BASE_URL,
            "note": "Stable Diffusion WebUI API 서버가 실행 중이어야 합니다."
        }
    }
