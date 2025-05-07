import os
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer

# ✅ 한국어 응답을 위한 프롬프트 템플릿 정의
prompt_template = PromptTemplate.from_template("""
당신은 Chick-Pay에 대해 잘 아는 금융 도우미입니다.
아래 문서를 참고하여 사용자의 질문에 **한국어로 친절하게** 답변하세요.

문서 내용:
{context}

질문:
{question}

답변 (한국어):
""")

# ✅ 벡터 DB 경로 설정
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_PATH = os.path.join(ROOT_DIR, "..", "vector_store")

# ✅ 임베딩 모델 (deprecate 대응한 최신 방식)
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ✅ FAISS 벡터 인덱스 로드
retriever = FAISS.load_local(
    folder_path=VECTOR_STORE_PATH,
    embeddings=embedding_model,
    allow_dangerous_deserialization=True
).as_retriever()

# ✅ LLM 구성 (Ollama LLaMA3)
llm = Ollama(model="llama3", temperature=0.2)

# ✅ Retrieval QA 체인 생성 (한국어 출력 지시어 포함)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt_template}
)

# ✅ 질문-응답 함수
def ask(question: str) -> str:
    return qa_chain.run(question)
