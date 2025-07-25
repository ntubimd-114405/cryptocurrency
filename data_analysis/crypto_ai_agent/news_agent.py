# crypto_ai_agent/news_agent.py
import os
from typing import Optional
from news.models import Article
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

def run_news_agent(
    question: str,
    db_path: str = "./vector_db/news",
    embed_model: str = "mxbai-embed-large",
    top_k: int = 5,
) -> str:
    vector_store = initialize_news_vector_store(db_location=db_path, model_name=embed_model)
    retriever: VectorStoreRetriever = vector_store.as_retriever(search_kwargs={"k": top_k})
    docs = retriever.invoke(question)
    results = []
    for doc in docs:
        meta = doc.metadata
        doc_id = getattr(doc, "id", None) or meta.get("id", "")
        results.append(f"{doc.page_content}（{meta.get('date', '')}）(id:{doc_id})")
    
    news_answer = generate_answer("\n".join(results), question)
    return news_answer


def generate_answer(content: str, question: str, model: str = "mistral") -> str:
    prompt = ChatPromptTemplate.from_template("""
    你是一位專業的加密貨幣分析顧問，請全程使用繁體中文回答。

    請根據以下資料，詳細回答這個問題：
    {question}

    以下是「新聞摘要」的資料，每則新聞後面都有對應的新聞 ID (id:xxx)，請在你的回答中明確引用相關新聞的 ID 以便對應來源：
    {content}
    """)

    llm = OllamaLLM(model=model)
    chain = prompt | llm
    result = chain.invoke({
        "question": question,
        "content": content
    })
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

    if not os.path.exists(os.path.join(db_location, "index")):
        documents, ids = [], []
        articles = Article.objects.filter(
            summary__isnull=False, content__isnull=False
        ).order_by("-time")[:max_docs]

        for article in articles:
            documents.append(Document(
                page_content=f"{article.title}\n\n{article.summary}",
                metadata={
                    "url": article.url,
                    "date": str(article.time),
                },
                id=str(article.id)
            ))
            ids.append(str(article.id))

        print(f"🧠 正在向量化 {len(documents)} 篇新聞...")
        vector_store.add_documents(documents, ids=ids)
        print("✅ 向量庫已建立並儲存")

    if test_query:
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        results = retriever.invoke(test_query)
        print("🔍 測試查詢結果：")
        for doc in results:
            meta = doc.metadata
            print(f"- {meta['date']} | {meta['website']} | {doc.page_content}")

    return vector_store