# build_knowledge_vectorstore.py
from knowledge_data import get_knowledge_documents
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

documents = get_knowledge_documents()
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# 建立 Chroma 向量資料庫（自動儲存到指定資料夾）
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="vector_db/knowledge_db"
)

print("✅ 知識資料庫建立完成")
