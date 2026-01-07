# Character AI - 인물 사진 캐릭터화 서비스

AI 기반 인물 이미지 캐릭터 변환 서비스 (기술 데모)

## Overview
인물 사진을 Stable Diffusion을 사용하여 다양한 스타일의 캐릭터 이미지로 변환하는 서비스입니다.

### 주요 기능
- **이미지 캐릭터화**: Stable Diffusion img2img를 사용하여 인물 사진을 캐릭터 이미지로 변환
- **다양한 스타일**: SD 캐릭터, 애니메이션, 반실사, 픽셀 아트, 카툰 스타일 지원
- **REST API**: iOS, Android, PC, 즉석사진관 등 멀티플랫폼 연동 가능

### 지원 플랫폼
- REST API (iOS, Android, PC, 즉석사진관 연동 가능)
- Web Demo UI

## Project Structure
```
├── backend/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config.py               # 환경 설정 (Pydantic Settings)
│   ├── routers/
│   │   └── transform.py        # 이미지 변환 API 엔드포인트
│   └── services/
│       └── stable_diffusion_service.py  # SD API 연동 서비스
├── static/
│   ├── index.html              # 웹 데모 UI
│   ├── styles.css              # 스타일시트
│   └── app.js                  # 프론트엔드 JavaScript
├── uploads/                    # 업로드된 원본 이미지
├── generated_images/           # 생성된 캐릭터 이미지
├── .env.example                # 환경 변수 예시
└── README.md                   # 프로젝트 문서
```

## API Endpoints
- `GET /api/transform/styles` - 사용 가능한 캐릭터 스타일 목록
- `POST /api/transform/character` - 인물 사진 캐릭터화
- `GET /api/transform/image/{image_id}` - 생성된 이미지 조회
- `GET /api/transform/original/{image_id}` - 원본 이미지 조회
- `GET /api/transform/health` - Stable Diffusion 서버 연결 상태

## Environment Variables
환경 변수는 `.env` 파일에서 관리됩니다. `.env.example`을 참고하세요.

- `STABLE_DIFFUSION_BASE_URL` - Stable Diffusion API 서버 주소
- `STABLE_DIFFUSION_API_KEY` - API 인증 키 (선택사항)
- `SD_DEFAULT_STEPS` - 기본 샘플링 스텝 수
- `SD_DEFAULT_CFG_SCALE` - 기본 CFG Scale
- `PORT` - 서버 포트

## Tech Stack
- Python 3.11 + FastAPI
- Stable Diffusion (AUTOMATIC1111 WebUI API)
- Pydantic Settings (환경 설정)
- httpx (비동기 HTTP 클라이언트)

## Running the App
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 5000
```

## Stable Diffusion Server
이 서비스는 별도의 Stable Diffusion 서버가 필요합니다.
AUTOMATIC1111 WebUI를 `--api` 옵션으로 실행하세요:
```bash
./webui.sh --api --listen --port 7860
```
