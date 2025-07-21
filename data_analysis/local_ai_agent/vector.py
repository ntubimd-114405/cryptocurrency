import os
import sys
import django

# 往上兩層才到 manage.py 同層的根目錄
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()


from typing import Optional
from news.models import Article
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import VectorStoreRetriever

def initialize_news_vector_store(
    db_location: str = "./vector_db/news",
    model_name: str = "mxbai-embed-large",
    max_docs: int = 100,
    test_query: Optional[str] = None
) -> Chroma:
    """
    初始化新聞資料的向量資料庫，若尚未建立則會從資料庫中取出新聞建立向量。

    參數：
    - db_location: 儲存向量資料庫的路徑
    - model_name: 使用的 Ollama 嵌入模型名稱
    - max_docs: 初次加入向量的最大新聞數量
    - test_query: 若提供則會執行查詢測試

    回傳：
    - vector_store: Chroma 向量資料庫實體
    """
    add_documents = not os.path.exists(db_location)

    embeddings = OllamaEmbeddings(model=model_name)

    vector_store = Chroma(
        collection_name="crypto_news_articles",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    if add_documents:
        documents = []
        ids = []

        articles = Article.objects.filter(
            summary__isnull=False,
            content__isnull=False
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


def create_qa_function(
    model_name: str = "mistral",
    embed_model: str = "mxbai-embed-large",
    db_path: str = "./vector_db/news",
    top_k: int = 5,
    prompt_template: Optional[str] = None,
):
    """
    建立一個 QA 函數 f(question: str) -> str，使用本地向量庫與 Ollama LLM 回答問題。

    回傳：
        qa_func: 一個函數，輸入問題字串，輸出回答字串。
    """

    vector_store = initialize_news_vector_store(
        db_location=db_path,
        model_name=embed_model,
        test_query=None,
    )
    retriever: VectorStoreRetriever = vector_store.as_retriever(search_kwargs={"k": top_k})

    if prompt_template is None:
        prompt_template = """
你是一位專業的加密貨幣新聞分析師，擅長根據新聞回答問題。

以下是相關新聞標題與摘要：
{reviews}

請根據以上內容回答以下問題：
{question}
"""

    llm = OllamaLLM(model=model_name)
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm

    def qa_func(question: str) -> str:
        docs = retriever.invoke(question)
        reviews = "\n".join(
            [f"- ({doc.metadata.get('date', '')}) {doc.page_content}" for doc in docs]
        )
        result = chain.invoke({"reviews": reviews, "question": question})
        
        return result.strip()

    return qa_func


# 測試範例
if __name__ == "__main__":
    qa = create_qa_function()
    while True:
        q = input("請輸入問題（輸入 q 離開）： ").strip()
        if q.lower() == "q":
            break
        answer = qa(q)
        print("🧠 回答：", answer)
