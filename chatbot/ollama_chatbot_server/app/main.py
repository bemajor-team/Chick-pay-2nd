from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests
import os

# 🧠 내부 챗봇 응답 (chick-pay 전용)
from app.llm_config import ask  # Ollama or OpenAI 연동된 함수

# 📦 FastAPI 앱 생성
app = FastAPI()

# 📁 정적 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "..", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 🏠 루트 페이지: chatbot.html 반환
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "AI.html"))

# 🌐 정부24 API 설정
SERVICE_KEY = "ClL9iwahzYFYieo2NCb0VBQa+DgLvATx4yBbyxYWLWcqC1k5ynsZSJ/NgGzAGrK/UVbZNgeyv2pESOn2uA/IUA=="
BASE_URL = "https://api.odcloud.kr/api/gov24/v3"

# 📬 메인 챗봇 API
@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        q = data.get("question", "")
        mode = data.get("support_mode", "list")

        # 🔍 불용어 제거 함수
        def extract_keywords(text):
            stopwords = ["알려줘", "좀", "해주세요", "같은", "정보", "뭐", "있어", "어떻게", "하는", "방법", "해줘", "해"]
            return " ".join([word for word in text.split() if word not in stopwords])

        # ✅ 키워드 추출
        keywords = extract_keywords(q)

        if data.get("support", False):
            # 정부24 API - 목록 조회
            if mode == "list":
                response = requests.get(
                    f"{BASE_URL}/serviceList",
                    params={
                        "serviceKey": SERVICE_KEY,
                        "page": 1,
                        "perPage": 10,
                        "cond[serviceName::LIKE]": keywords
                    }
                )
                print("🔍 요청 URL:", response.url)
                print("📥 응답 데이터:", response.json())

                data_json = response.json()

                if data_json.get("code") != 0:
                    return {
                        "answer": f"정부24 API 오류: {data_json.get('msg', '알 수 없는 오류')}"
                    }

                services = data_json.get("data", [])
                if not services:
                    return {
                        "answer": f"'{q}' 관련 지원금 정보를 찾지 못했습니다."
                    }

                formatted = [
                    f"\U0001F4CC {s.get('서비스명', '제목 없음')} ({s.get('제공기관명', '기관정보 없음')})"
                    for s in services
                ]
                return {
                    "type": "지원금목록",
                    "answer": "\n".join(formatted)
                }

            # 정부24 API - 상세 조회
            elif mode == "detail":
                response = requests.get(
                    f"{BASE_URL}/serviceDetail",
                    params={
                        "serviceKey": SERVICE_KEY,
                        "cond[serviceId::LIKE]": keywords
                    }
                )
                return {
                    "type": "지원금상세",
                    "result": response.json()
                }

            else:
                return {"error": "Invalid support_mode"}

        else:
            # 🧠 LLM 응답 (기초적인 예외 처리 포함)
            try:
                answer = ask(q)
                if not answer or answer.strip() == "":
                    answer = f"'{q}'에 대한 답변을 준비 중입니다."
            except Exception as e:
                answer = f"답변 중 오류 발생: {str(e)}"

            return {"question": q, "answer": answer}

    except Exception as e:
        return {"error": str(e)}
