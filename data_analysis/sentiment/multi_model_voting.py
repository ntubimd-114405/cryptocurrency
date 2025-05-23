import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 只顯示錯誤


import torch
from transformers import pipeline
from transformers import AutoTokenizer
from collections import Counter
import tensorflow as tf
import logging

tf.debugging.set_log_device_placement(False)
tf.get_logger().setLevel('ERROR')
logging.getLogger("transformers").setLevel(logging.ERROR)



# 建立 sentiment pipeline 快取池
sentiment_pipelines = {}

def get_sentiment_pipeline(model_name, device):
    if model_name not in sentiment_pipelines:
        sentiment_pipelines[model_name] = pipeline(
            "sentiment-analysis",
            model=model_name,
            device=device
        )
    return sentiment_pipelines[model_name]

def split_long_text(text, tokenizer, max_tokens=512):
    tokens = tokenizer.tokenize(text)
    chunks = []
    while tokens:
        chunk = tokens[:max_tokens]
        chunks.append(tokenizer.convert_tokens_to_string(chunk))
        tokens = tokens[max_tokens:]
    return chunks

def analyze_sentiment(text, model_name, sentiment_map, device, max_length=512):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    text_chunks = split_long_text(text, tokenizer, max_tokens=max_length)

    results = []
    for chunk in text_chunks:
        pipeline_model = get_sentiment_pipeline(model_name, device)
        result = pipeline_model(chunk, truncation=True, max_length=max_length)[0]
        label = result['label']
        score = result['score']
        
        if score <= 0.66:
            continue
        
        sentiment_number = sentiment_map.get(label, '0')
        results.append(sentiment_number)

    # 多段落投票
    return majority_vote(results) if results else "-9"


def majority_vote(results_list):
    vote_counts = Counter(results_list)
    most_common = vote_counts.most_common()
    max_count = most_common[0][1]
    top_labels = [label for label, count in most_common if count == max_count]
    return '0' if len(top_labels) > 1 else top_labels[0]

def predict_sentiment(text):
    print("Start prediction")
    models_info = [
        ("ElKulako/cryptobert", {"Bearish": "-1", "Neutral": "0", "Bullish": "1"}),
        ("mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis", {"positive": "1", "negative": "-1", "neutral": "0"}),
        ("AfterRain007/cryptobertRefined", {"Bullish": "1", "Bearish": "-1", "Neutral": "0"}),
        ("ProsusAI/finbert", {"positive": "1", "negative": "-1", "neutral": "0"})
    ]

    device = 0 if torch.cuda.is_available() else -1
    all_sentiments = []

    for model_name, sentiment_map in models_info:
        print(f"Evaluating with model: {model_name}")
        sentiment = analyze_sentiment(text, model_name, sentiment_map, device)
        if sentiment != "-9":
            all_sentiments.append(sentiment)

    print("Sentiments:", all_sentiments)
    return majority_vote(all_sentiments) if all_sentiments else "0"

if __name__ == "__main__":
    test_texts = [
        "The Bitcoin market is too volatile to trust." * 10,
        "Ethereum just surged after BlackRock announced their support.",
        "The crypto industry is facing increasing regulations and uncertainty."
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"\n[Sample {i}]")
        result = predict_sentiment(text)
        print("Predicted sentiment:", result)

