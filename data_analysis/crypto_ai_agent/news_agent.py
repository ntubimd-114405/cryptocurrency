import os
from typing import Optional
from datetime import datetime
from news.models import Article
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


def initialize_news_vector_store(
    db_location: str = "./vector_db/news",
    model_name: str = "mxbai-embed-large",
    max_docs: int = 100,
) -> Chroma:
    embeddings = OllamaEmbeddings(model=model_name)

    vector_store = Chroma(
        collection_name="crypto_news_articles",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    # 取得已存在的向量庫 ID
    existing_ids = set(vector_store.get()["ids"])

    # 找最新的新聞
    articles = Article.objects.filter(
        summary__isnull=False, content__isnull=False
    ).order_by("-time")[:max_docs]

    documents, ids = [], []
    for article in articles:
        aid = str(article.id)  # 使用 Django 原本的 id
        if aid in existing_ids:
            continue  # 避免重複
        # 只存 title + summary
        documents.append(Document(
            page_content=f"{article.title}\n{article.summary}",
            metadata={
                "url": article.url,
                "date": str(article.time.date()),  # ISO 格式方便查詢
            },
            id=aid
        ))
        ids.append(aid)

    if documents:
        print(f"🧠 新增 {len(documents)} 篇新聞到向量庫...")
        vector_store.add_documents(documents, ids=ids)
        print("✅ 向量庫已更新")
    else:
        print("⚡ 向量庫已是最新，無需更新")

    return vector_store


def search_news(
    question: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: str = "./vector_db/news",
    embed_model: str = "mxbai-embed-large",
    top_k: int = 5,
):
    #vector_store = initialize_news_vector_store(db_location=db_path, model_name=embed_model) 每次搜尋都要重整向量庫

    embeddings = OllamaEmbeddings(model=embed_model)
    vector_store = Chroma(
        collection_name="crypto_news_articles",
        persist_directory=db_path,
        embedding_function=embeddings,
    )
    # --- 時間過濾條件 ---
    where = None
    date_filters = []
    if start_date:
        start_timestamp = int(datetime.fromisoformat(start_date).timestamp())
        date_filters.append({"date": {"$gte": start_timestamp}})
    if end_date:
        end_timestamp = int(datetime.fromisoformat(end_date).timestamp())
        date_filters.append({"date": {"$lte": end_timestamp}})
    if date_filters:
        where = {"$and": date_filters} if len(date_filters) > 1 else date_filters[0]
    print(f"🔍 搜尋條件：{where}")

    # --- 相似度搜尋 ---
    docs = vector_store.similarity_search(
        query=question,
        k=top_k,
        filter=where
    )

    # 只取 title / summary / id
    results = []
    for doc in docs:
        parts = doc.page_content.split("\n", 1)
        title = parts[0] if len(parts) > 0 else ""
        summary = parts[1] if len(parts) > 1 else ""

        results.append({
            "id": doc.id,  # 使用 Django DB 的 id
            "title": title,
            "summary": summary,
        })

    return results
