import os
import django
import sys

# 初始化 Django 環境
sys.path.append(os.path.dirname(__file__))  # 指向 manage.py 同層目錄
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()

from news.models import Article
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# 向量資料庫儲存路徑
db_location = "./vector_db/news"
add_documents = not os.path.exists(db_location)

# 使用 Ollama 的嵌入模型
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# 只第一次建立需要加入 document
if add_documents:
    documents = []
    ids = []

    articles = Article.objects.filter(
        summary__isnull=False,
        content__isnull=False
    ).order_by("-time")[:100]

    for article in articles:
        doc = Document(
            page_content=f"{article.title or ''}",
            metadata={
                "url": article.url,
                "date": str(article.time),
                #"sentiment": article.sentiment or "neutral",
                "website": article.website.name,
                #"icon": article.website.icon_url,
            },
            id=str(article.id)
        )
        documents.append(doc)
        ids.append(str(article.id))

# 初始化 Chroma 向量資料庫
vector_store = Chroma(
    collection_name="crypto_news_articles",
    persist_directory=db_location,
    embedding_function=embeddings,
)

# 寫入向量
if add_documents:
    print(f"🧠 向量化 {len(documents)} 篇新聞資料中...")
    vector_store.add_documents(documents=documents, ids=ids)
    print("✅ 成功建立姿勢庫並儲存")

# 測試查詢
retriever = vector_store.as_retriever(search_kwargs={"k": 5})
results = retriever.invoke("比特幣為何在六月中上漲？")

print("🔍 測試查詢結果：")
for doc in results:
    meta = doc.metadata
    print(f"- {meta['date']} | {meta['website']} | {doc.page_content[:60]}...")
