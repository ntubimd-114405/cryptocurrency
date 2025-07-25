from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

# 初始化嵌入模型
embedding = OllamaEmbeddings(model="mxbai-embed-large")

# 正確讀取向量資料庫
vectorstore = Chroma(
    persist_directory="vector_db/knowledge_db",
    embedding_function=embedding  # ✅ 正確寫法是 embedding_function
)

# 建立 Retriever
retriever = vectorstore.as_retriever()

# 初始化 LLM
llm = OllamaLLM(model="deepseek-r1:1.5b")

# 測試問題
question = "什麼是適合積極型投資人的幣種配置？"

# 檢索資料
docs = retriever.invoke(question)
context = "\n".join([doc.page_content for doc in docs])

# Prompt 建立
prompt = PromptTemplate.from_template("""
你是加密貨幣投資助理，根據以下資料回答使用者問題。

參考資料：
{context}

使用者問題：
{question}

請以簡潔、清楚的方式回答。
""")

# 組合 Prompt 並產生回答
final_prompt = prompt.format(context=context, question=question)
answer = llm.invoke(final_prompt)

print("📌 問題：", question)
print("🤖 回答：", answer)
