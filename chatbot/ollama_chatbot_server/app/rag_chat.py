from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI
from pydantic import BaseModel
import faiss
import os
import requests
from sentence_transformers import SentenceTransformer
import pickle

app = FastAPI()
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "..", "static")  # 📌 상위 디렉토리 기준

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_chat():
    return FileResponse(os.path.join(STATIC_DIR, "chatbot.html"))


# Load vector DB
index = faiss.read_index("vector_store.index")
with open("doc_texts.pkl", "rb") as f:
    doc_texts = pickle.load(f)

class Message(BaseModel):
    user_message: str

@app.post("/chat")
async def chat(message: Message):
    query = message.user_message
    query_vector = model.encode([query])
    D, I = index.search(query_vector, k=3)

    # Top-3 문서 조합
    context = "\n".join([doc_texts[i] for i in I[0]])

    # RAG 프롬프트 구성
    prompt = f"""
당신은 chick-pay.com의 금융 챗봇입니다.
절대 영어, 중국어, 일본어 등 외국어를 사용하지 마세요.
오직 한국어로만 답변해야 합니다. 이건 매우 중요합니다.

다음은 내부 문서에서 검색된 정보입니다:

{context}

사용자 질문: {query}

상기 문서를 참고하여 정확하고 부드러운 **한국어 문장**으로만 응답하세요.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    answer = response.json()["response"]
    return {"response": answer}
