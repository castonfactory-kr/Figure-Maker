import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.routers import transform

app = FastAPI(
    title="Character & Figure AI API",
    description="AI-powered character transformation and 3D model generation service",
    version="1.0.0"
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
    return {"status": "healthy", "service": "character-figure-ai"}


@app.get("/api/info")
async def api_info():
    return {
        "name": "Character & Figure AI API",
        "version": "1.0.0",
        "endpoints": {
            "transform_character": "POST /api/transform/character",
            "get_styles": "GET /api/transform/styles",
            "get_image": "GET /api/transform/image/{image_id}",
            "create_3d_model": "POST /api/transform/3d-model",
            "get_3d_status": "GET /api/transform/3d-model/status/{task_id}"
        },
        "description": "Upload a portrait photo and transform it into stylized characters. Then generate 3D models from those characters."
    }
