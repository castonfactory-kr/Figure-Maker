# Character & Figure AI - Tech Demo

AI 기반 인물 이미지 캐릭터화 및 3D 피규어 모델 생성 서비스

## Overview
이 프로젝트는 인물 사진을 다양한 스타일의 캐릭터로 변환하고, 해당 캐릭터 이미지를 기반으로 3D 모델을 생성하는 AI Wrapper 서비스입니다.

### 주요 기능
1. **이미지 캐릭터화**: OpenAI gpt-image-1을 사용하여 인물 사진을 SD 캐릭터, 애니메이션, 반실사 등 다양한 스타일로 변환
2. **3D 모델 생성**: Meshy AI API를 통해 캐릭터 이미지에서 3D 모델(.glb, .fbx) 생성

### 지원 플랫폼
- REST API (iOS, Android, PC, 즉석사진관 연동 가능)
- Web Demo UI

## Project Structure
```
├── backend/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── routers/
│   │   └── transform.py     # 변환 API 엔드포인트
│   └── services/
│       ├── openai_service.py  # OpenAI 이미지 생성 서비스
│       └── meshy_service.py   # Meshy 3D 모델 생성 서비스
├── static/
│   ├── index.html           # 웹 데모 UI
│   ├── styles.css           # 스타일시트
│   └── app.js               # 프론트엔드 JavaScript
├── uploads/                 # 업로드된 원본 이미지
├── generated_images/        # 생성된 캐릭터 이미지
└── generated_models/        # 생성된 3D 모델 파일
```

## API Endpoints
- `GET /api/transform/styles` - 사용 가능한 캐릭터 스타일 목록
- `POST /api/transform/character` - 인물 사진 캐릭터화
- `GET /api/transform/image/{image_id}` - 생성된 이미지 조회
- `POST /api/transform/3d-model` - 3D 모델 생성 시작
- `GET /api/transform/3d-model/status/{task_id}` - 3D 모델 생성 상태 확인

## Environment Variables
- `AI_INTEGRATIONS_OPENAI_API_KEY` - Replit AI Integration (자동 설정)
- `AI_INTEGRATIONS_OPENAI_BASE_URL` - Replit AI Integration (자동 설정)
- `MESHY_API_KEY` - Meshy AI API 키 (선택사항, 3D 모델 생성용)

## Tech Stack
- Python 3.11 + FastAPI
- OpenAI gpt-image-1 (Replit AI Integration)
- Meshy AI (3D 모델 생성)

## Running the App
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 5000
```
