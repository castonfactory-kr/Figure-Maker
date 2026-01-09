# CastAI - AI 캐릭터 변환 서비스

AI 기반 인물 이미지 캐릭터 변환 서비스 (포토부스 키오스크 연동)

## Overview
인물 사진을 Stable Diffusion을 사용하여 다양한 스타일의 캐릭터 이미지로 변환하는 서비스입니다.

### 주요 기능
- **이미지 캐릭터화**: Stable Diffusion img2img를 사용하여 인물 사진을 캐릭터 이미지로 변환
- **3가지 스타일**: 리얼(버블헤드), 반실사(3D), 캐릭터(동화풍) 지원
- **REST API**: iOS, Android, PC, 포토부스 키오스크 연동 가능
- **갤러리 기능**: 생성된 이미지 보기, 다운로드, 삭제 지원

### 지원 플랫폼
- REST API (iOS, Android, PC, 포토부스 키오스크 연동 가능)
- Web Demo UI
- 키오스크 전용 UI (스타일 선택, 결제 화면)

### 회사 정보
- **브랜드**: CastAI (임시)
- **회사명**: Cast on factory
- **Instagram**: @caston_factory

## Project Structure
```
├── app/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config.py               # 환경 설정 (Pydantic Settings)
│   ├── models/                 # 데이터 모델
│   │   └── schemas.py
│   ├── routers/                # API 라우터
│   │   └── transform.py        # 이미지 변환 API 엔드포인트
│   └── services/               # 비즈니스 로직
│       └── stable_diffusion.py # SD API 연동 서비스
├── static/
│   ├── index.html              # 메인 웹 데모 UI
│   ├── styles.css              # 메인 스타일시트
│   ├── app.js                  # 메인 프론트엔드 JavaScript
│   ├── kiosk-select.html       # 키오스크 스타일 선택 화면
│   ├── kiosk-payment.html      # 키오스크 결제 화면 (더미)
│   ├── kiosk.css               # 키오스크 전용 스타일
│   └── kiosk.js                # 키오스크 전용 JavaScript
├── uploads/                    # 업로드된 원본 이미지
├── generated_images/           # 생성된 캐릭터 이미지
├── .env.example                # 환경 변수 예시
└── README.md                   # 프로젝트 문서
```

## 캐릭터 스타일 (3종)
1. **리얼 (버블헤드)** - 실사풍 큰 머리 캐릭터 (real_bubblehead)
2. **반실사 (3D)** - 3D 애니메이션 스타일 (semi_realistic)
3. **캐릭터** - 동화풍 캐릭터 스타일 (character)

## API Endpoints
- `GET /api/transform/styles` - 사용 가능한 캐릭터 스타일 목록
- `POST /api/transform/character` - 인물 사진 캐릭터화
- `GET /api/transform/image/{image_id}` - 생성된 이미지 조회
- `DELETE /api/transform/image/{image_id}` - 생성된 이미지 삭제
- `GET /api/transform/original/{image_id}` - 원본 이미지 조회
- `GET /api/transform/gallery` - 생성된 이미지 갤러리
- `GET /api/transform/health` - Stable Diffusion 서버 연결 상태
- `GET /docs` - FastAPI 자동 생성 API 문서

## 키오스크 페이지 (더미)
- `/static/kiosk-select.html` - 스타일 선택 화면 (와이드 스크린용)
- `/static/kiosk-payment.html` - 결제 화면 (신용카드/간편결제 더미 애니메이션)

## Environment Variables
환경 변수는 Replit Secrets 또는 `.env` 파일에서 관리됩니다.

- `STABLE_DIFFUSION_BASE_URL` - Stable Diffusion API 서버 주소
- `STABLE_DIFFUSION_API_KEY` - API 인증 키 (선택사항)
- `SD_DEFAULT_STEPS` - 기본 샘플링 스텝 수 (기본: 45)
- `SD_DEFAULT_CFG_SCALE` - 기본 CFG Scale (기본: 24)
- `SD_DEFAULT_SAMPLER` - 기본 샘플러 (기본: Euler a)

## Tech Stack
- Python 3.11 + FastAPI
- Stable Diffusion (AUTOMATIC1111 WebUI API)
- Pydantic Settings (환경 설정)
- httpx (비동기 HTTP 클라이언트)

## Running the App
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```

## Stable Diffusion Server
이 서비스는 별도의 Stable Diffusion 서버가 필요합니다.
AUTOMATIC1111 WebUI를 `--api` 옵션으로 실행하세요:
```bash
./webui.sh --api --listen --port 17860
```

**참고**: 한국 가정용 ISP는 8080 등 일반 포트를 차단할 수 있습니다. 17860 같은 비표준 포트 사용을 권장합니다.

## Recent Changes (2026-01-09)
- 캐릭터 스타일 4종 → 3종으로 변경 (리얼/반실사/캐릭터)
- 메인 페이지 CastAI로 리브랜딩
- API 문서 섹션 제거 (FastAPI /docs 사용)
- 푸터에 회사 정보 추가 (Cast on factory, @caston_factory)
- 포토부스 키오스크용 더미 페이지 2종 추가
- 갤러리 모달 기능 추가 (이미지 확대, 다운로드, 삭제)
