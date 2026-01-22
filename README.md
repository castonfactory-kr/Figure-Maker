# Figure-Maker

**Character AI Service** - 커스텀 LoRA 등 파인튜닝된 Stable Diffusion 1.5를 이용한 인물사진 변환 서비스  
img2img AI 활용 예시 키오스크 UX 데모 프로젝트

> **마이그레이션 히스토리**: Stable Diffusion WebUI(AUTOMATIC1111)에서 **ComfyUI**로 마이그레이션되었습니다.

---

## 주요 기능

### 🎨 3가지 캐릭터 스타일

- **리얼 (버블헤드)**: 실사풍 큰 머리 캐릭터
- **디즈니 (3D)**: 디즈니/픽사 애니메이션 스타일
- **치비 (넨도로이드)**: 귀여운 피규어 스타일

### 🖥️ 키오스크 워크플로우

7단계 사용자 여정으로 구성된 웹 데모 UI:

```
시작 → 스타일 선택 → 촬영/업로드 → 미리보기 → 배송 정보 → 결제 → 출력
```

### 🔌 REST API

멀티플랫폼 통합을 위한 FastAPI 기반 REST API 제공

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│                  (Web Kiosk Demo - 키오스크 UX 시연용)              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Application Layer                             │
│                   (FastAPI + REST API)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ /api/        │  │ /api/        │  │ Health Check           │ │
│  │ transform/   │  │ transform/   │  │ /health                │ │
│  │ character    │  │ styles       │  │                        │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI Layer                                   │
│                   (ComfyUI Server)                              │
│         - Workflow 기반 이미지 생성                                 │
│         - Stable Diffusion 1.5 모델                              │
│         - 커스텀 LoRA/파인튜닝 모델 지원                              │
└─────────────────────────────────────────────────────────────────┘
```

**데이터 흐름**:  
이미지 업로드 → ComfyUI 워크플로우 실행 → AI 변환 처리 → 결과 반환

**비동기 처리**:  
httpx 기반 비차단 AI 처리로 안정적인 성능 제공

---

## 기술 스택

| 구분            | 기술                                              |
| --------------- | ------------------------------------------------- |
| **백엔드**      | Python 3.11, FastAPI 0.128+, Uvicorn              |
| **AI 엔진**     | ComfyUI (Stable Diffusion 1.5 기반)               |
| **프론트엔드**  | HTML5, CSS3, Vanilla JavaScript                   |
| **비동기 처리** | httpx 0.28+, aiofiles 25.1+                       |
| **재시도 로직** | tenacity 9.1+                                     |
| **이미지 처리** | Pillow 10.1+                                      |
| **설정 관리**   | Pydantic Settings 2.12+                           |
| **배포**        | Docker, GitHub Actions, GitHub Container Registry |

---

## 로컬 개발환경 설정

### 1. 사전 요구사항

- Python 3.11 이상
- ComfyUI 서버 (별도 실행 필요)
- Git

### 2. 프로젝트 클론 및 설정

```bash
# 저장소 클론
git clone <repository-url>
cd Figure-Maker

# 가상환경 생성 및 활성화
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env
```

`.env` 파일을 편집하여 ComfyUI 서버 주소를 설정합니다:

```env
COMFYUI_BASE_URL=http://localhost:8188
```

### 4. 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

### 5. 접속

- **웹 UI**: http://localhost:5000
- **API 문서 (Swagger)**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health

---

## ComfyUI 서버 설정

> **중요**: 이 프로젝트는 Stable Diffusion WebUI(AUTOMATIC1111)에서 **ComfyUI로 마이그레이션** 되었습니다.

### 1. ComfyUI 설치

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
```

### 2. 모델 설치

다음 모델을 ComfyUI 디렉토리에 배치합니다:

- **Checkpoint**: `dreamshaper_8.safetensors` → `models/checkpoints/`
- **VAE**: `vaeFtMse840000EmaPruned_vaeFtMse840k.safetensors` → `models/vae/`

> 모델 다운로드: [Hugging Face](https://huggingface.co/) 또는 [Civitai](https://civitai.com/)에서 다운로드 가능

### 3. ComfyUI 실행

```bash
# 기본 실행 (로컬호스트만)
python main.py

# API 모드 + 외부 접속 허용
python main.py --listen 0.0.0.0 --port 8188
```

### 4. 네트워크 설정 (선택사항)

- **기본 포트**: 8188 (프로젝트 `.env`에서 `COMFYUI_BASE_URL`로 설정)
- **외부 접속**: 방화벽/공유기 포트포워딩 설정 필요

### 5. 연결 확인

```bash
# ComfyUI 서버 상태 확인
curl http://localhost:8188/system_stats
```

또는 Figure-Maker API를 통해 확인:

```bash
curl http://localhost:5000/api/transform/health
```

---

## REST API 문서

### 기본 URL

```
http://localhost:5000/api
```

### 엔드포인트

#### 1. 스타일 목록 조회

```http
GET /api/transform/styles
```

**응답 예시:**

```json
{
  "styles": {
    "real_bubblehead": {
      "name": "리얼 (버블헤드)",
      "name_en": "Real (Bubble Head)",
      "description": "실사풍 큰 머리 캐릭터"
    },
    "semi_realistic": {
      "name": "디즈니 (3D)",
      "name_en": "Disney (3D)",
      "description": "디즈니/픽사 애니메이션 스타일"
    },
    "character": {
      "name": "치비 (넨도로이드)",
      "name_en": "Chibi (Nendoroid)",
      "description": "귀여운 피규어 스타일"
    }
  },
  "recommended_strength": 0.22
}
```

#### 2. 캐릭터 변환

```http
POST /api/transform/character
Content-Type: multipart/form-data
```

**파라미터:**
| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `image` | File | O | 인물 이미지 파일 (JPG, PNG 등) |
| `style` | String | X | 스타일 ID (기본값: `real_bubblehead`) |
| `denoising_strength` | Float | X | 변환 강도 (기본값: 스타일별 최적값) |

**응답 예시:**

```json
{
  "success": true,
  "original_id": "abc123-def456",
  "image_id": "xyz789-uvw012",
  "image_url": "api/transform/image/xyz789-uvw012",
  "original_url": "api/transform/original/abc123-def456",
  "style": "semi_realistic"
}
```

#### 3. 생성된 이미지 조회

```http
GET /api/transform/image/{image_id}
```

PNG 형식의 생성된 캐릭터 이미지를 반환합니다.

#### 4. 원본 이미지 조회

```http
GET /api/transform/original/{image_id}
```

업로드된 원본 이미지를 반환합니다.

#### 5. 이미지 삭제

```http
DELETE /api/transform/image/{image_id}
```

**응답 예시:**

```json
{
  "success": true,
  "message": "이미지가 삭제되었습니다"
}
```

#### 6. Health Check

```http
GET /api/transform/health
```

ComfyUI 서버 연결 상태를 확인합니다.

**응답 예시:**

```json
{
  "status": "connected",
  "server_info": { ... },
  "base_url": "http://localhost:8188"
}
```

---

## 클라이언트 연동 예시

### cURL

```bash
curl -X POST "http://localhost:5000/api/transform/character" \
  -F "image=@photo.jpg" \
  -F "style=semi_realistic"
```

### Python

```python
import requests

with open("photo.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:5000/api/transform/character",
        files={"image": f},
        data={"style": "character"}
    )
    result = response.json()
    print(f"생성 이미지: {result['image_url']}")
```

### JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append("image", imageFile);
formData.append("style", "real_bubblehead");

const response = await fetch("/api/transform/character", {
  method: "POST",
  body: formData,
});
const result = await response.json();
console.log("Image URL:", result.image_url);
```

---

## 프로젝트 구조

```
Figure-Maker/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 애플리케이션 진입점
│   ├── config.py               # 환경 설정 (Pydantic Settings)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # API 요청/응답 스키마
│   ├── routers/
│   │   ├── __init__.py
│   │   └── transform.py        # 이미지 변환 API 라우터
│   └── services/
│       ├── __init__.py
│       └── stable_diffusion.py # ComfyUI API 통합 서비스
├── static/
│   ├── index.html              # 메인 화면 (시작)
│   ├── style.html              # 스타일 선택
│   ├── camera.html             # 사진 촬영/업로드
│   ├── preview.html            # 결과 미리보기
│   ├── shipping.html           # 배송 정보 입력
│   ├── payment.html            # 결제 화면
│   ├── printing.html           # 출력 완료
│   ├── kiosk.css               # 키오스크 스타일시트
│   └── images/                 # UI 이미지 에셋
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD
├── uploads/                    # 업로드된 원본 이미지 (자동 생성)
├── generated_images/           # AI 생성 이미지 (자동 생성)
├── workflow_template.json      # ComfyUI 워크플로우 템플릿
├── Dockerfile                  # Docker 컨테이너 설정
├── requirements.txt            # Python 의존성
├── pyproject.toml              # 프로젝트 메타데이터
├── .env.example                # 환경 변수 템플릿
├── .gitignore
└── README.md                   # 프로젝트 문서
```

---

## 배포 가이드

### Docker를 사용한 배포

#### 1. Docker 이미지 빌드 및 실행

```bash
# 이미지 빌드
docker build -t figure-maker .

# 컨테이너 실행
docker run -p 5000:5000 --env-file .env figure-maker
```

#### 2. Docker Compose 사용 (권장)

```yaml
# docker-compose.yml
version: "3.8"

services:
  backend:
    image: ghcr.io/your-username/figure-maker:latest
    ports:
      - "5000:5000"
    environment:
      - COMFYUI_BASE_URL=http://comfyui-server:8188
    volumes:
      - ./uploads:/app/uploads
      - ./generated_images:/app/generated_images
```

```bash
docker compose up -d
```

### GitHub Actions 자동 배포

이 프로젝트는 GitHub Actions를 통한 자동 배포를 지원합니다.

**배포 흐름**:

1. `main` 브랜치에 코드 푸시
2. GitHub Actions가 Docker 이미지 빌드
3. GitHub Container Registry(GHCR)에 이미지 푸시
4. SSH를 통해 배포 서버 접속
5. `backend` 서비스로 docker-compose 업데이트

**필요한 GitHub Secrets**:

- `DOCKER_USERNAME`: GitHub 사용자명
- `DOCKER_PASSWORD`: GitHub Personal Access Token
- `HOST`: 배포 서버 주소
- `USERNAME`: SSH 사용자명
- `KEY`: SSH 개인 키
- `PORT`: SSH 포트

---

## 환경 변수

| 변수명                     | 설명                   | 기본값                         | 필수 |
| -------------------------- | ---------------------- | ------------------------------ | ---- |
| `COMFYUI_BASE_URL`         | ComfyUI 서버 주소      | `http://castonfactory.kr:8880` | O    |
| `STABLE_DIFFUSION_API_KEY` | API 인증 키 (선택)     | -                              | X    |
| `UPLOAD_DIR`               | 업로드 디렉터리        | `uploads`                      | X    |
| `GENERATED_IMAGES_DIR`     | 생성 이미지 디렉터리   | `generated_images`             | X    |
| `MAX_FILE_SIZE_MB`         | 최대 파일 크기 (MB)    | `10`                           | X    |
| `APP_ROOT_PATH`            | 애플리케이션 루트 경로 | `""`                           | X    |

---

## 라이선스

본 프로젝트는 별도 ComfyUI 서버와 통신하는 API 클라이언트 방식으로, Stable Diffusion 모델을 직접 포함하지 않습니다.

**주요 의존성 라이선스**:

- FastAPI: MIT License
- Python 라이브러리들: MIT / Apache 2.0

본 프로젝트는 **기술 데모/참고용 프로젝트**로 제공됩니다. 추후 사용자가 필요에 따라 라이선스를 선택할 수 있습니다.

---

## 문제 해결

### ComfyUI 연결 실패

```bash
# ComfyUI 서버 상태 확인
curl http://localhost:8188/system_stats

# .env 파일의 COMFYUI_BASE_URL 확인
cat .env
```

### 이미지 생성 타임아웃

- ComfyUI 서버의 GPU 메모리 확인
- `denoising_strength` 값을 낮춰서 시도 (0.1 ~ 0.3)
- ComfyUI 서버 로그 확인

### 포트 충돌

```bash
# 다른 포트로 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 기여 및 문의

본 프로젝트는 img2img AI 활용 예시를 위한 데모 프로젝트입니다.  
문의사항이나 개선 제안이 있으시면 이슈를 등록해 주세요.

---

**Powered by FastAPI + ComfyUI + Stable Diffusion 1.5**
