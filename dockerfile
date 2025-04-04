# Python 기반 이미지
FROM python:3.10-slim

# 작업 디렉토리 생성
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 8000 포트 사용
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
