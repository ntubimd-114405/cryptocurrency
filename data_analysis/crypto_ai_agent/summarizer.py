from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

def generate_section_answer(section_name: str, content: str, question: str, model: str = "mistral") -> str:
    prompt = ChatPromptTemplate.from_template(f"""
你是一位專業的加密貨幣分析顧問，並且只會用中文回答。
                                              
請根據之後的資料，詳細回答以下問題：
{question}

以下是「{section_name}」的資料：
{content}


""")
    llm = OllamaLLM(model=model)
    chain = prompt | llm
    result = chain.invoke({
        "question": question
    })
    print(result)
    return result.strip()

def summarize_all_individual(
    question: str,
    news: str,
    price: str,
    survey: str,
    model: str = "mistral"
) -> str:
    news_answer = generate_section_answer("新聞摘要", news, question, model)
    price_answer = generate_section_answer("加密貨幣價格資訊", price, question, model)
    survey_answer = generate_section_answer("使用者背景資料", survey, question, model)

    combined_answer = (
        "以下是根據不同資料來源分別產生的回答：\n\n"
        "【新聞摘要】\n" + news_answer + "\n\n"
        "【加密貨幣價格資訊】\n" + price_answer + "\n\n"
        "【使用者背景資料】\n" + survey_answer
    )

    return combined_answer
