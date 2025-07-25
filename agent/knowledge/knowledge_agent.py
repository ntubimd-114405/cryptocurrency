# agent/knowledge_agent.py
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

# 嵌入模型 + Chroma 向量資料庫
embedding = OllamaEmbeddings(model="mxbai-embed-large")
vectorstore = Chroma(
    persist_directory="vector_db/knowledge_db",
    embedding_function=embedding
)
retriever = vectorstore.as_retriever()
llm = OllamaLLM(model="deepseek-r1:1.5b")  # ← 你已安裝的模型名稱

# 包裝成函式
def ask_knowledge_agent(question: str) -> str:
    docs = retriever.invoke(question)
    if not docs:
        return "查無相關知識內容，請嘗試重新提問。"

    context = "\n".join([doc.page_content for doc in docs])
    prompt = PromptTemplate.from_template("""
你是加密貨幣投資助理，根據以下資料回答使用者問題。

參考資料：
{context}

使用者問題：
{question}

請以簡潔、清楚的方式回答。
""")
    final_prompt = prompt.format(context=context, question=question)
    answer = llm.invoke(final_prompt)
    return answer
