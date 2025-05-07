import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

chat_history = []

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "..", "static")), name="static")

@app.get("/")
async def serve_chatbot():
    return FileResponse(os.path.join(BASE_DIR, "..", "static", "chatbot.html"))

class Message(BaseModel):
    user_message: str

@app.post("/chat")
async def chat(message: Message):
    # RAG 문서 검색 (내부 knowledge.json 사용)
    context = retrieve_context(message.user_message, top_k=1)
    
    # 강화된 한국어-only 프롬프트
    prompt = (
        "너는 절대 외국어를 사용하지 않는, 오직 한국어로만 답변하는 금융 챗봇이야.\n"
        "아래 문서를 참고해서 사용자 질문에 대해 공손하고 부드러운 한국어로만 응답해.\n"
        "영어, 중국어, 일본어는 절대 사용하지 마. 이건 아주 중요해.\n"
        f"[문서]{context[0]}"
        f"[질문]{message.user_message}"
        "정확하고 친절한 한국어로 대답해줘."
    )

    for chat in chat_history:
        prompt_text += f"{chat['content']}"

    prompt_text += "\n이어서 대답해줘."

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt_text,
                "stream": False
            },
            timeout=60
        )
        data = response.json()
    except requests.exceptions.RequestException as e:
        print("Ollama 연결 실패:", e)
        return {"response": "⚠️ 챗봇 응답에 실패했습니다. 서버 상태를 확인해주세요."}

    chat_history.append({"role": "assistant", "content": data["response"]})

    return {"response": data["response"]}