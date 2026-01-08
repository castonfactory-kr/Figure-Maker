# Character AI - 인물 사진 캐릭터화 서비스

AI 기반 인물 이미지를 다양한 스타일의 캐릭터 이미지로 변환하는 기술 데모 서비스입니다.

## 주요 기능

- **4가지 캐릭터 스타일 지원**
  - SD 캐릭터 (치비) - 귀여운 2등신 캐릭터
  - 반실사 (3D) - 3D 애니메이션 스타일
  - 애니메이션 - 일본 애니메이션 스타일
  - 카툰 - 만화 캐릭터 스타일

- **REST API** - iOS, Android, PC, 즉석사진관 등 멀티플랫폼 연동 가능
- **Web Demo UI** - 브라우저에서 바로 테스트 가능

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Web Demo      │   Mobile Apps   │   Photo Booth System        │
│   (HTML/JS)     │   (iOS/Android) │   (API Integration)         │
└────────┬────────┴────────┬────────┴─────────────┬───────────────┘
         │                 │                       │
         ▼                 ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     REST API (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ /transform/  │  │ /transform/  │  │ /transform/            │ │
│  │ character    │  │ styles       │  │ image/{id}             │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Stable Diffusion Server                         │
│                  (AUTOMATIC1111 WebUI API)                       │
│                  - img2img Transformation                        │
│                  - Style-based Prompting                         │
└─────────────────────────────────────────────────────────────────┘
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI Engine** | Stable Diffusion (AUTOMATIC1111 WebUI) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **API Protocol** | REST (JSON) |

---

## 로컬 개발환경 설정

### 1. 사전 요구사항

- Python 3.11 이상
- Stable Diffusion WebUI (AUTOMATIC1111) 서버

### 2. 프로젝트 클론

```bash
git clone <repository-url>
cd character-ai
```

### 3. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Linux/Mac)
source venv/bin/activate

# 활성화 (Windows)
venv\Scripts\activate
```

### 4. 의존성 설치

```bash
pip install -r requirements.txt
```

### 5. 환경 변수 설정

`.env.example`을 참고하여 `.env` 파일을 생성합니다:

```bash
cp .env.example .env
```

`.env` 파일을 편집하여 SD 서버 주소를 설정합니다:

```env
STABLE_DIFFUSION_BASE_URL=http://your-sd-server:17860
SD_DEFAULT_MODEL=v1-5-pruned-emaonly
SD_DEFAULT_SAMPLER=Euler a
SD_DEFAULT_STEPS=45
SD_DEFAULT_CFG_SCALE=24.0
```

### 6. 서버 실행

```bash
# 개발 모드 (자동 리로드)
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# 프로덕션 모드
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```

브라우저에서 `http://localhost:5000` 접속

---

## Stable Diffusion 서버 설정

이 서비스는 별도의 Stable Diffusion 서버가 필요합니다.

### AUTOMATIC1111 WebUI 설치

```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
```

### API 모드로 실행

```bash
# Linux/Mac
./webui.sh --api --listen --port 17860

# Windows
webui.bat --api --listen --port 17860
```

| 옵션 | 설명 |
|------|------|
| `--api` | REST API 활성화 |
| `--listen` | 외부 접속 허용 (0.0.0.0 바인딩) |
| `--port 17860` | 포트 지정 |

> **참고**: 한국 가정용 ISP는 8080 등 일반 포트를 차단할 수 있습니다. 17860 같은 비표준 포트 사용을 권장합니다.

### 외부 접속 설정 (선택)

외부에서 SD 서버에 접속하려면:
1. PC 방화벽에서 포트 열기
2. 공유기 포트포워딩 설정
3. (필요시) ISP에 공인 IP 요청

---

## REST API 문서

### 기본 URL
```
http://your-server:5000/api
```

### 엔드포인트

#### 1. 스타일 목록 조회
```http
GET /api/transform/styles
```

**응답 예시:**
```json
{
  "styles": [
    {"id": "sd_character", "name": "SD 캐릭터 (치비)", "description": "귀여운 2등신 캐릭터"},
    {"id": "semi_realistic", "name": "반실사 (3D)", "description": "3D 애니메이션 스타일"},
    {"id": "anime", "name": "애니메이션", "description": "일본 애니메이션 스타일"},
    {"id": "cartoon", "name": "카툰 스타일", "description": "만화 캐릭터 스타일"}
  ]
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
| `image` | File | O | 인물 이미지 파일 |
| `style` | String | X | 스타일 ID (기본: sd_character) |
| `denoising_strength` | Float | X | 변환 강도 0.3~0.9 (기본: 0.42) |

**응답 예시:**
```json
{
  "success": true,
  "original_id": "abc123",
  "image_id": "xyz789",
  "image_url": "/api/transform/image/xyz789",
  "original_url": "/api/transform/original/abc123",
  "style": "anime"
}
```

#### 3. 생성된 이미지 조회
```http
GET /api/transform/image/{image_id}
```

#### 4. 원본 이미지 조회
```http
GET /api/transform/original/{image_id}
```

#### 5. 갤러리 (최근 생성 이미지)
```http
GET /api/transform/gallery
```

#### 6. SD 서버 연결 상태
```http
GET /api/transform/health
```

---

## 클라이언트 연동 예시

### cURL
```bash
curl -X POST "http://localhost:5000/api/transform/character" \
  -F "image=@photo.jpg" \
  -F "style=anime" \
  -F "denoising_strength=0.42"
```

### Python
```python
import requests

with open("photo.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:5000/api/transform/character",
        files={"image": f},
        data={"style": "sd_character", "denoising_strength": 0.42}
    )
    result = response.json()
    print(f"캐릭터 이미지: {result['image_url']}")
```

### JavaScript
```javascript
const formData = new FormData();
formData.append('image', imageFile);
formData.append('style', 'anime');
formData.append('denoising_strength', '0.42');

const response = await fetch('/api/transform/character', {
    method: 'POST',
    body: formData
});
const result = await response.json();
```

---

## 프로젝트 구조

```
├── app/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config.py               # 환경 설정 (Pydantic Settings)
│   ├── models/
│   │   └── schemas.py          # 데이터 모델
│   ├── routers/
│   │   └── transform.py        # API 라우터
│   └── services/
│       └── stable_diffusion.py # SD API 연동 서비스
├── static/
│   ├── index.html              # 웹 데모 UI
│   ├── styles.css              # 스타일시트
│   └── app.js                  # 프론트엔드 JavaScript
├── uploads/                    # 업로드된 원본 이미지
├── generated_images/           # 생성된 캐릭터 이미지
├── .env                        # 환경 변수 (Git 제외)
├── .env.example                # 환경 변수 템플릿
├── requirements.txt            # Python 의존성
└── README.md                   # 프로젝트 문서
```

---

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `STABLE_DIFFUSION_BASE_URL` | SD API 서버 주소 | - |
| `STABLE_DIFFUSION_API_KEY` | API 인증 키 (선택) | - |
| `SD_DEFAULT_MODEL` | 기본 모델 체크포인트 | v1-5-pruned-emaonly |
| `SD_DEFAULT_SAMPLER` | 샘플러 | Euler a |
| `SD_DEFAULT_STEPS` | 샘플링 스텝 수 | 45 |
| `SD_DEFAULT_CFG_SCALE` | CFG Scale | 24.0 |
| `UPLOAD_DIR` | 업로드 디렉터리 | uploads |
| `GENERATED_IMAGES_DIR` | 생성 이미지 디렉터리 | generated_images |
| `MAX_FILE_SIZE_MB` | 최대 파일 크기 | 10 |

---

## 라이선스

이 프로젝트는 기술 데모 목적으로 제작되었습니다.
