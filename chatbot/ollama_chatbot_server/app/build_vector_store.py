from sentence_transformers import SentenceTransformer
import faiss
import pickle

documents = [
    "Chick Pay는 가장 귀여운 금융 서비스로 간편하고 안전하게 이용할 수 있는 금융 서비스입니다.",
    "송금은 로그인 후 송금하기 버튼을 눌러, Chick Pay에 가입된 상대방의 이메일 주소와 송금 금액을 입력하여 진행합니다.",
    "OTP 인증은 2차 인증 수단으로, 보안 강화를 위해 사용됩니다.",
    "마이페이지에서는 본인의 계좌 잔액을 실시간으로 확인할 수 있습니다."
]

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
vectors = model.encode(documents)

index = faiss.IndexFlatL2(vectors.shape[1])
index.add(vectors)
faiss.write_index(index, "vector_store.index")

with open("doc_texts.pkl", "wb") as f:
    pickle.dump(documents, f)

