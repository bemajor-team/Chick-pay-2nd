FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치를 위해 먼저 requirements.txt 복사
COPY requirements.txt ./

# 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 서버 실행 (Django 기준)
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "my_project.wsgi:application"]