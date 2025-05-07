from sentence_transformers import SentenceTransformer
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 문서 로딩 및 분할
loader = PyPDFLoader("documents/finance_faq.pdf")
pages = loader.load_and_split()

# 임베딩 생성
model = SentenceTransformer("all-MiniLM-L6-v2")
texts = [page.page_content for page in pages]
embeddings = model.encode(texts)

# 벡터 저장
db = FAISS.from_texts(texts, model)
db.save_local("vector_store")
