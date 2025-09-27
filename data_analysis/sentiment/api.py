from langchain_ollama import OllamaLLM

# 全局初始化 LLM，避免每次呼叫都初始化
_llm_instance = OllamaLLM(model="mistral")

def predict_sentiment_api(text: str) -> tuple[str, float]:
    """
    使用 OllamaLLM 做金融新聞情緒分析。
    
    Returns:
        (sentiment, confidence)
        sentiment: '1' = 正面, '0' = 中立, '-1' = 負面, '-9' = 無法判斷
        confidence: 0.0 ~ 1.0
    """
    if not text or not text.strip():
        return '-9', 0.0  # 空文本直接回傳容錯結果

    prompt = f"""
You are a financial news sentiment analysis assistant.
Please respond ONLY with one of the following: "Positive", "Neutral", or "Negative".
Do not include any extra text.

News content:
{text}
"""

    try:
        # 使用全局 LLM 實例
        output = _llm_instance.invoke(prompt).strip()
        normalized = output.lower().replace(" ", "")

        mapping = {
            'positive': '1',
            'neutral': '0',
            'negative': '-1'
        }

        sentiment = mapping.get(normalized, '-9')
        confidence = 0.9 if sentiment in ['1', '0', '-1'] else 0.0

        return sentiment, confidence

    except Exception as e:
        print(f"OllamaLLM analysis error: {e}")
        return '-9', 0.0  # 容錯回傳
