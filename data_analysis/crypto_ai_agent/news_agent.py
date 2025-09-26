import os
from typing import Optional
from datetime import datetime
from news.models import Article
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

def search_news(
    question: str,
    db_path: str = "./vector_db/news",
    embed_model: str = "mxbai-embed-large",
    top_k: int = 5,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    vector_store = initialize_news_vector_store(db_location=db_path, model_name=embed_model)
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
        filter=where  # 使用 filter 參數
    )
    
    results = []
    for doc in docs:
        meta = doc.metadata
        doc_id = getattr(doc, "id", None) or meta.get("id", "")
        results.append(f"(id:{doc_id}){doc.page_content}")
    
    return generate_answer("\n".join(results), question)

def generate_answer(content: str, question: str, model: str = "mistral") -> str:
    prompt = ChatPromptTemplate.from_template("""
        你是一位專業的加密貨幣分析顧問，請全程使用繁體中文回答。

        請根據以下資料，詳細回答這個問題：
        {question}

        以下是「新聞摘要」的資料，每則新聞前面都有對應的新聞 ID (id:xxx) 和日期，
        請在你的回答中明確引用相關新聞的 ID，並按照以下格式輸出：
        (id:xxx) (日期) - 新聞內容
        {content}
        """)
    llm = OllamaLLM(model=model)
    chain = prompt | llm
    result = chain.invoke({"question": question, "content": content})
    return result.strip()


def initialize_news_vector_store(
    db_location: str = "./vector_db/news",
    model_name: str = "mxbai-embed-large",
    max_docs: int = 100,
    test_query: Optional[str] = None
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
        if str(article.id) in existing_ids:
            continue  # 避免重複
        documents.append(Document(
            page_content=(f"{article.title}\n{article.summary}\n{article.content}")[:512],
            metadata={
                "url": article.url,
                "date": str(article.time.date()),  # ISO 格式方便查詢
            },
            id=str(article.id)
        ))
        ids.append(str(article.id))

    if documents:
        print(f"🧠 新增 {len(documents)} 篇新聞到向量庫...")
        vector_store.add_documents(documents, ids=ids)
        print("✅ 向量庫已更新")
    else:
        print("⚡ 向量庫已是最新，無需更新")

    if test_query:
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        results = retriever.invoke(test_query)
        print("🔍 測試查詢結果：")
        for doc in results:
            meta = doc.metadata
            print(f"- {meta.get('date')} | {meta.get('url')} | {doc.page_content}")

    return vector_store

