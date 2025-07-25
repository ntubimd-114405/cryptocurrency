# crypto_ai_agent/vector_store.py

import os
from typing import Optional
from news.models import Article
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma  # ✅ 正確
from langchain_core.documents import Document

def initialize_news_vector_store(
    db_location: str = "./vector_db/news",
    model_name: str = "mxbai-embed-large",
    max_docs: int = 100,
    test_query: Optional[str] = None
) -> Chroma:
    add_documents = not os.path.exists(db_location)
    embeddings = OllamaEmbeddings(model=model_name)

    vector_store = Chroma(
        collection_name="crypto_news_articles",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    if add_documents:
        documents, ids = [], []
        articles = Article.objects.filter(
            summary__isnull=False, content__isnull=False
        ).order_by("-time")[:max_docs]

        for article in articles:
            doc = Document(
                page_content=f"{article.title or ''}",
                metadata={
                    "url": article.url,
                    "date": str(article.time),
                    "website": article.website.name,
                },
                id=str(article.id)
            )
            documents.append(doc)
            ids.append(str(article.id))

        print(f"🧠 向量化 {len(documents)} 篇新聞資料中...")
        vector_store.add_documents(documents=documents, ids=ids)
        print("✅ 成功建立姿勢庫並儲存")

    if test_query:
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        results = retriever.invoke(test_query)
        print("🔍 測試查詢結果：")
        for doc in results:
            meta = doc.metadata
            print(f"- {meta['date']} | {meta['website']} | {doc.page_content}")

    return vector_store
