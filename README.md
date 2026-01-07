# Character AI - 인물 사진 캐릭터화 서비스

AI 기반 인물 이미지 캐릭터 변환 서비스의 기술 데모입니다.

## 📋 프로젝트 개요

이 프로젝트는 인물 사진을 다양한 스타일의 캐릭터 이미지로 변환하는 AI Wrapper 서비스입니다.

### 주요 기능
- **이미지 캐릭터화**: Stable Diffusion을 사용하여 인물 사진을 캐릭터 이미지로 변환
- **다양한 스타일 지원**: SD 캐릭터(치비), 애니메이션, 반실사(Pixar), 픽셀 아트, 카툰 스타일
- **REST API 제공**: iOS, Android, PC, 즉석사진관 등 다양한 플랫폼에서 연동 가능

### 지원 플랫폼
- 웹 브라우저 (데모 UI)
- REST API를 통한 모든 플랫폼 지원
  - iOS / Android 앱
  - PC 애플리케이션
  - 즉석사진관 시스템 연동

---

## 🏗️ 시스템 아키텍처

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

---

## 📁 프로젝트 구조

```
character-ai/
├── backend/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config.py               # 환경 설정 관리
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
├── .env                        # 환경 변수 (생성 필요)
└── README.md                   # 이 문서
```

---

## ⚙️ 환경 설정

### 1. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 설정값을 수정합니다:

```bash
cp .env.example .env
```

### 2. 주요 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `STABLE_DIFFUSION_BASE_URL` | Stable Diffusion API 서버 주소 | `http://127.0.0.1:7860` |
| `STABLE_DIFFUSION_API_KEY` | API 인증 키 (선택사항) | - |
| `SD_DEFAULT_STEPS` | 샘플링 스텝 수 | `30` |
| `SD_DEFAULT_CFG_SCALE` | CFG Scale | `7.0` |
| `PORT` | 서버 포트 | `5000` |

---

## 🖥️ Stable Diffusion 서버 설정

이 서비스는 별도의 Stable Diffusion 서버가 필요합니다.

### AUTOMATIC1111 WebUI 설치 및 실행

1. **설치**
   ```bash
   git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
   cd stable-diffusion-webui
   ```

2. **API 모드로 실행**
   ```bash
   # Windows
   webui.bat --api
   
   # Linux/Mac
   ./webui.sh --api
   ```

3. **외부 접속 허용 (VPS 환경)**
   ```bash
   ./webui.sh --api --listen --port 7860
   ```

4. **API 인증 추가 (선택사항)**
   ```bash
   ./webui.sh --api --api-auth username:password
   ```

### 권장 모델
- Stable Diffusion 1.5 또는 2.1
- 캐릭터화 특화 모델 (예: Anything V5, CounterfeitV3 등)

---

## 🚀 실행 방법

### 개발 환경

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python -m uvicorn backend.main:app --host 0.0.0.0 --port 5000 --reload
```

### 프로덕션 환경 (VPS)

```bash
# Gunicorn으로 실행
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000

# 또는 systemd 서비스로 등록
sudo systemctl start character-ai
```

---

## 📡 REST API 문서

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
  "styles": {
    "sd_character": {"name": "SD 캐릭터 (치비)", "name_en": "SD Character (Chibi)"},
    "anime": {"name": "애니메이션", "name_en": "Anime Style"},
    "semi_realistic": {"name": "반실사 (Pixar)", "name_en": "Semi-Realistic (Pixar)"},
    "pixel_art": {"name": "픽셀 아트", "name_en": "Pixel Art"},
    "cartoon": {"name": "카툰 스타일", "name_en": "Cartoon Style"}
  }
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
| `image` | File | ✅ | 인물 이미지 파일 |
| `style` | String | ❌ | 스타일 ID (기본: sd_character) |
| `denoising_strength` | Float | ❌ | 변환 강도 0.3~0.9 (기본: 0.7) |

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

#### 3. 이미지 조회
```http
GET /api/transform/image/{image_id}
```

#### 4. 서버 상태 확인
```http
GET /api/transform/health
```

---

## 📱 클라이언트 연동 예시

### cURL
```bash
curl -X POST "http://localhost:5000/api/transform/character" \
  -F "image=@photo.jpg" \
  -F "style=anime" \
  -F "denoising_strength=0.7"
```

### Python
```python
import requests

with open("photo.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:5000/api/transform/character",
        files={"image": f},
        data={"style": "sd_character", "denoising_strength": 0.7}
    )
    result = response.json()
    print(f"캐릭터 이미지: {result['image_url']}")
```

### JavaScript (React/React Native)
```javascript
const formData = new FormData();
formData.append('image', imageFile);
formData.append('style', 'anime');
formData.append('denoising_strength', '0.7');

const response = await fetch('/api/transform/character', {
    method: 'POST',
    body: formData
});
const result = await response.json();
```

### Swift (iOS)
```swift
let url = URL(string: "http://your-server:5000/api/transform/character")!
var request = URLRequest(url: url)
request.httpMethod = "POST"

let boundary = UUID().uuidString
request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

// ... multipart body 구성
```

---

## 🔧 기술 스택

| 구분 | 기술 |
|------|------|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI Engine** | Stable Diffusion (AUTOMATIC1111 WebUI) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **API Protocol** | REST (JSON) |
| **Deployment** | VPS (Linux), Docker (선택) |

---

## 📝 향후 개발 계획

- [ ] 3D 피규어 모델 생성 기능 (Meshy AI 연동)
- [ ] Flutter 기반 모바일 앱 개발
- [ ] 즉석사진관 전용 SDK 개발
- [ ] 배치 처리 및 대기열 시스템
- [ ] 사용자 인증 및 이용 기록 관리

---

## 🤝 연동 문의

즉석사진관 서비스 연동 또는 API 사용에 대한 문의는 담당자에게 연락해주세요.

---

## 📄 라이선스

이 프로젝트는 기술 데모 목적으로 개발되었습니다.
