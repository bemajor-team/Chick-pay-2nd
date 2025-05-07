from fastapi import FastAPI, Request
from llm_config import ask

app = FastAPI()

@app.get("/ask")
async def query(q: str):
    answer = ask(q)
    return {"question": q, "answer": answer}
