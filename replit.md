# CastAI - AI 캐릭터 변환 서비스

AI 기반 인물 이미지 캐릭터 변환 서비스 (포토부스 키오스크 연동)

## Overview
인물 사진을 Stable Diffusion을 사용하여 다양한 스타일의 캐릭터 이미지로 변환하는 서비스입니다.

### 주요 기능
- **이미지 캐릭터화**: Stable Diffusion img2img를 사용하여 인물 사진을 캐릭터 이미지로 변환
- **4가지 스타일**: 리얼(버블헤드), 반실사(3D), 캐릭터(동화풍), 애니메이션 지원
- **REST API**: iOS, Android, PC, 포토부스 키오스크 연동 가능
- **갤러리 기능**: 생성된 이미지 보기, 다운로드, 삭제 지원

### 지원 플랫폼
- REST API (iOS, Android, PC, 포토부스 키오스크 연동 가능)
- Web Demo UI
- 키오스크 전용 UI (밝은 테마, 터치 친화적)

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
│   ├── kiosk.css               # 키오스크 전용 스타일 (라이트 모드)
│   ├── kiosk-upload.html       # 키오스크 사진 업로드 화면
│   ├── kiosk-style.html        # 키오스크 스타일 선택 화면
│   ├── kiosk-shipping.html     # 키오스크 배송지 입력 화면
│   ├── kiosk-payment.html      # 키오스크 결제 화면
│   ├── kiosk-printing.html     # 키오스크 인쇄중 화면
│   └── images/                 # 스타일 예시 이미지 (placeholder)
├── uploads/                    # 업로드된 원본 이미지
├── generated_images/           # 생성된 캐릭터 이미지
└── README.md                   # 프로젝트 문서
```

## 캐릭터 스타일 (4종)
1. **리얼 (버블헤드)** - 실사풍 큰 머리 캐릭터 (real_bubblehead)
2. **반실사 (3D)** - 3D 애니메이션 스타일 (semi_realistic)
3. **캐릭터** - 동화풍 캐릭터 스타일 (character)
4. **애니메이션** - 일본 애니메이션 스타일 (anime)

## 키오스크 페이지 플로우
1. `/static/kiosk-upload.html` - 사진 업로드
2. `/static/kiosk-style.html` - 스타일 선택 (좌: 업로드 이미지, 우: 4종 스타일)
3. `/static/kiosk-shipping.html` - 배송지 입력
4. `/static/kiosk-payment.html` - 결제 (신용카드/간편결제)
5. `/static/kiosk-printing.html` - 사진 인쇄중

## 키오스크 UI 특징
- **라이트 모드**: 흰색, 크림, 베이지, 파스텔 톤
- **터치 친화적**: 큰 버튼, 넓은 터치 영역
- **16:9 와이드 스크린 최적화**
- **스타일 예시 이미지**: `/static/images/` 폴더에 수동 추가 필요
  - style-real.jpg
  - style-3d.jpg
  - style-character.jpg
  - style-anime.jpg

## API Endpoints
- `GET /api/transform/styles` - 사용 가능한 캐릭터 스타일 목록
- `POST /api/transform/character` - 인물 사진 캐릭터화
- `GET /api/transform/image/{image_id}` - 생성된 이미지 조회
- `DELETE /api/transform/image/{image_id}` - 생성된 이미지 삭제
- `GET /api/transform/gallery` - 생성된 이미지 갤러리
- `GET /api/transform/health` - Stable Diffusion 서버 연결 상태
- `GET /docs` - FastAPI 자동 생성 API 문서

## Tech Stack
- Python 3.11 + FastAPI
- Stable Diffusion (AUTOMATIC1111 WebUI API)
- Pydantic Settings (환경 설정)
- httpx (비동기 HTTP 클라이언트)

## Running the App
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```

## Recent Changes (2026-01-12)
- 키오스크 UI 전면 개편: 다크 모드 → 라이트 모드 (파스텔 톤)
- 키오스크 페이지 플로우 구현: 업로드 → 스타일 선택 → 배송지 → 결제 → 인쇄중
- 캐릭터 스타일 4종으로 확장 (애니메이션 추가)
- 스타일 선택 화면: 좌측 업로드 이미지, 우측 스타일 선택 (예시 이미지 placeholder)
