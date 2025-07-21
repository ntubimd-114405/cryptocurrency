# crypto_ai_agent/qa_agent.py

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import VectorStoreRetriever
from .vector_store import initialize_news_vector_store
from .user_context import get_user_questionnaire_context
from typing import Optional
from django.contrib.auth.models import User

def create_qa_function(
    model_name: str = "mistral",
    embed_model: str = "mxbai-embed-large",
    db_path: str = "./vector_db/news",
    top_k: int = 5,
    prompt_template: Optional[str] = None,
):
    vector_store = initialize_news_vector_store(
        db_location=db_path,
        model_name=embed_model,
        test_query=None,
    )
    retriever: VectorStoreRetriever = vector_store.as_retriever(search_kwargs={"k": top_k})

    if prompt_template is None:
        prompt_template = """
    你是一位專業的加密貨幣與金融心理分析顧問。

    請參考以下內容：

    使用者背景資訊如下：
    {user_context}

    以下是與問題相關的新聞摘要（包含標題與來源）：
    {reviews}

    請根據上述使用者背景與新聞摘要，用「條列分段」形式回答使用者的問題：
    1. 每段說明一個面向。
    2. 每段都需引用一則新聞標題與來源。
    3. 使用自然流暢的中文回答。
    4. 若可行，也可整合使用者背景與新聞內容進行深入分析。

    問題如下：
    {question}
    """

    llm = OllamaLLM(model=model_name)
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm

    def qa_func(question: str, user: Optional[User] = None) -> str:
        docs = retriever.invoke(question)
        reviews = "\n".join(
            [f"- ({doc.metadata.get('date', '')}) {doc.page_content}" for doc in docs]
        )
        user_context = get_user_questionnaire_context(user) if user else "（無使用者背景）"
        print(len(user_context),len(reviews))
        result = chain.invoke({
            "reviews": reviews,
            "question": question,
            "user_context": user_context,
        })
        return result.strip()

    return qa_func
