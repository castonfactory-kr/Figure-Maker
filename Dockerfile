# Python 3.11 버전 사용 (README.md 요구사항 준수)
FROM python:3.11-slim

# 작업 폴더 설정
WORKDIR /app

# 필요한 디렉토리 생성
RUN mkdir -p uploads generated_images

# 패키지 목록 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 5000

# 실행 명령어 (app.main:app으로 수정)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]