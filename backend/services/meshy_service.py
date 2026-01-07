import httpx
import os
import asyncio
from typing import Optional

MESHY_API_KEY = os.environ.get("MESHY_API_KEY")
MESHY_BASE_URL = "https://api.meshy.ai/v1"


class MeshyService:
    def __init__(self):
        self.api_key = MESHY_API_KEY
        self.base_url = MESHY_BASE_URL
    
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_3d_model_from_image(self, image_url: str, name: str = "character") -> Optional[dict]:
        if not self.api_key:
            return {
                "status": "demo_mode",
                "message": "Meshy API key not configured. In demo mode, showing placeholder.",
                "task_id": "demo_task_id",
                "preview_url": None
            }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "image_url": image_url,
                "enable_pbr": True,
                "ai_model": "meshy-4",
                "topology": "quad",
                "target_polycount": 30000,
            }
            
            response = await client.post(
                f"{self.base_url}/image-to-3d",
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 202:
                data = response.json()
                return {
                    "status": "processing",
                    "task_id": data.get("result"),
                    "message": "3D model generation started"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to start 3D generation: {response.text}"
                }
    
    async def get_task_status(self, task_id: str) -> dict:
        if task_id == "demo_task_id":
            return {
                "status": "demo_mode",
                "message": "Demo mode - no actual 3D model generated",
                "progress": 100
            }
        
        if not self.api_key:
            return {"status": "error", "message": "Meshy API key not configured"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/image-to-3d/{task_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": data.get("status"),
                    "progress": data.get("progress", 0),
                    "model_urls": data.get("model_urls", {}),
                    "thumbnail_url": data.get("thumbnail_url")
                }
            else:
                return {
                    "status": "error", 
                    "message": f"Failed to get status: {response.text}"
                }
    
    async def download_model(self, model_url: str) -> Optional[bytes]:
        if not model_url:
            return None
            
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(model_url)
            if response.status_code == 200:
                return response.content
            return None


meshy_service = MeshyService()
