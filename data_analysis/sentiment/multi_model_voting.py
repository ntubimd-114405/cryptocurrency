import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 只顯示錯誤訊息

import torch
from transformers import pipeline, AutoTokenizer
import logging

# 關閉 transformers 的警告訊息
logging.getLogger("transformers").setLevel(logging.ERROR)

# 建立 sentiment pipeline 快取池，避免重複載入模型
sentiment_pipelines = {}

def get_sentiment_pipeline(model_name, device):
    """取得或建立指定模型的 sentiment pipeline"""
    if model_name not in sentiment_pipelines:
        sentiment_pipelines[model_name] = pipeline(
            "sentiment-analysis",
            model=model_name,
            device=device
        )
    return sentiment_pipelines[model_name]


def split_long_text(text, tokenizer, max_tokens=512):
    """將長文本切割成不超過 max_tokens 的小段落"""
    tokens = tokenizer.tokenize(text)
    chunks = []
    while tokens:
        chunk = tokens[:max_tokens]
        chunks.append(tokenizer.convert_tokens_to_string(chunk))
        tokens = tokens[max_tokens:]
    return chunks


def analyze_sentiment_weighted(text, model_name, sentiment_map, device, max_length=512):
    """
    【方案一】模型內加權平均法：
    - 對每段文字進行情緒預測
    - 依照情緒值 × score 計算加權分數
    - 取所有段落的平均作為該模型的最終分數
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    text_chunks = split_long_text(text, tokenizer, max_tokens=max_length)

    pipeline_model = get_sentiment_pipeline(model_name, device)
    total_weighted_score = 0.0
    count = 0

    for chunk in text_chunks:
        result = pipeline_model(chunk, truncation=True, max_length=max_length)[0]
        label = result['label']
        score = result['score']
        sentiment_value = float(sentiment_map.get(label, 0))  # 將 label 映射為情緒值 (-1, 0, 1)
        weighted_score = sentiment_value * score  # 加權分數
        print(f"[{model_name}] Label: {label}, Score: {score:.4f}, Weighted: {weighted_score:.4f}")
        total_weighted_score += weighted_score
        count += 1

    # 計算模型的平均分數
    avg_score = total_weighted_score / count if count else 0.0

    # 根據閾值決定模型的最終情緒結果
    if avg_score > 0.2:
        sentiment = 1
    elif avg_score < -0.2:
        sentiment = -1
    else:
        sentiment = 0

    print(f"→ {model_name} 平均情緒分數：{avg_score:.4f}，判斷結果：{sentiment}")
    return avg_score  # 回傳平均加權分數（非整數）


def predict_sentiment(text):
    """
    【方案二】跨模型加權平均法：
    - 先使用方案一，取得每個模型的平均情緒分數
    - 再取所有模型的平均值，作為最終整體情緒判斷
    """
    print("\n=== Start prediction ===")
    models_info = [
        # 模型名稱與其 label 對應的數值映射
        ("ElKulako/cryptobert", {"Bearish": -1, "Neutral": 0, "Bullish": 1}),
        ("mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis", {"positive": 1, "negative": -1, "neutral": 0}),
        ("AfterRain007/cryptobertRefined", {"Bullish": 1, "Bearish": -1, "Neutral": 0}),
        ("ProsusAI/finbert", {"positive": 1, "negative": -1, "neutral": 0})
    ]

    device = 0 if torch.cuda.is_available() else -1  # 如果有 GPU 使用 GPU，否則使用 CPU
    model_scores = []

    # 逐一執行每個模型的分析
    for model_name, sentiment_map in models_info:
        print(f"\nEvaluating with model: {model_name}")
        score = analyze_sentiment_weighted(text, model_name, sentiment_map, device)
        model_scores.append(score)

    # 計算所有模型的平均分數
    final_score = sum(model_scores) / len(model_scores) if model_scores else 0.0

    # 決定最終情緒分類
    if final_score > 0.2:
        final_sentiment = "1"   # 正面
    elif final_score < -0.2:
        final_sentiment = "-1"  # 負面
    else:
        final_sentiment = "0"   # 中立

    print(f"\n=== 最終加權平均分數：{final_score:.4f}，預測結果：{final_sentiment} ===\n")
    return (final_sentiment,final_score)


if __name__ == "__main__":
    # 測試文本清單，涵蓋不同情緒情境
    test_texts = [
        # 範例一：偏正面
        # 說明：內容描述正面消息（政策支持、技術創新），
        # 預期結果 → 正面（1）
        "Bitcoin surged today as major financial institutions announced new support for crypto regulations. "
        "This move is expected to boost investor confidence and attract more institutional capital into the market.",

        # 範例二：偏負面
        # 說明：內容強調市場下跌、投資者恐慌，
        # 預期結果 → 負面（-1）
        "The cryptocurrency market crashed over 15% today amid growing regulatory fears. "
        "Investors are worried about stricter government policies and uncertain future for digital assets.",

        # 範例三：中立新聞報導
        # 說明：內容較為客觀，僅描述市場狀況與事件，未帶強烈情緒，
        # 預期結果 → 中立（0）
        "Ethereum’s trading volume remained stable this week, with slight fluctuations in price. "
        "Analysts suggest the market is waiting for further economic data before taking a direction."
# 本週以太坊交易量維持穩定，價格略有波動。
# “分析師認為，市場正在等待進一步的經濟數據，然後再決定方向。”
    ]

    # 對每段文字進行情緒預測
    for i, text in enumerate(test_texts, 1):
        print(f"\n[Sample {i}]")
        result = predict_sentiment(text)
        print(f"Predicted sentiment: {result}")
