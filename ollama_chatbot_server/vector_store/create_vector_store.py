import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document

# ✅ 문서 정의 (필요 시 더 추가 가능)
docs = [
    Document(page_content="Chick-Pay는 송금, 인증, 잔액 확인 기능을 제공하는 금융 서비스입니다."),
    # Document(page_content="송금 기능은 OTP 인증을 기반으로 작동합니다."),
    Document(page_content="정부 지원금 정보는 청년내일채움공제, 청년희망적금 등이 있습니다."),
    Document(page_content="Chick-Pay는 보안 강화를 위해 OTP 인증을 요구합니다."),
    Document(page_content="사용자는 Chick-Pay를 통해 간편하게 잔액을 확인할 수 있습니다.")
]

# ✅ 임베딩 모델 초기화
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ✅ FAISS 인덱스 생성
faiss_index = FAISS.from_documents(docs, embedding_model)

# ✅ 저장 경로 설정
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_PATH = os.path.join(ROOT_DIR, "vector_store")

# ✅ 인덱스 저장 (.faiss, .pkl 파일 생성됨)
faiss_index.save_local(SAVE_PATH)
print(f"[✅] 벡터 인덱스 저장 완료: {SAVE_PATH}")
