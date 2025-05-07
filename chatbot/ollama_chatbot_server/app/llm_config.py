from langchain.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from sentence_transformers import SentenceTransformer

# 모델 로딩
llm = Ollama(model="llama3", temperature=0.2)
retriever = FAISS.load_local("vector_store", SentenceTransformer("all-MiniLM-L6-v2")).as_retriever()

# RAG Chain 구성
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

def ask(question):
    return qa_chain.run(question)
