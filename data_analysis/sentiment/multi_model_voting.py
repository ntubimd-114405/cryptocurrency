import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 只顯示錯誤


import pandas as pd
from transformers import pipeline
from collections import Counter
import tensorflow as tf
import logging
import torch
from tqdm import tqdm

tf.debugging.set_log_device_placement(False)
tf.get_logger().setLevel('ERROR')
logging.getLogger("transformers").setLevel(logging.ERROR)

def analyze_sentiment(text, model_name, sentiment_map,max_length=512):
    device = 0 if torch.cuda.is_available() else -1  # 優先使用 GPU
    torch.cuda.set_device(device)  # Explicitly set the device for CUDA

    # Initialize the sentiment analysis pipeline
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model=model_name,
        device=device  # Use the selected device (GPU or CPU)
    )
    result = sentiment_pipeline(text, truncation=True, max_length=max_length)[0]
    label = result['label']
    score = result['score']
    sentiment_number = sentiment_map.get(label, '0')  # 默認為 '0'
    if score<=0.8:
        sentiment_number = "-9"
    return sentiment_number

def majority_vote(results_list):
    vote_counts = Counter(results_list)
    most_common = vote_counts.most_common()
    max_count = most_common[0][1]
    top_labels = [label for label, count in most_common if count == max_count]
    return '0' if len(top_labels) > 1 else top_labels[0]

def split_text(text, max_length=512):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def predict_sentiment(text):
    models_info = [
        ("ElKulako/cryptobert", {"Bearish": "-1", "Neutral": "0", "Bullish": "1"}),
        ("mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis", {"positive": "1", "negative": "-1", "neutral": "0"}),
        ("AfterRain007/cryptobertRefined", {"Bullish": "1", "Bearish": "-1", "Neutral": "0"}),
        ("ProsusAI/finbert", {"positive": "1", "negative": "-1", "neutral": "0"})
    ]
    
    text_segments = split_text(text)  # 拆分長文本
    all_sentiments = []
    for model_name, sentiment_map in tqdm(models_info, desc="Processing models", leave=False):
        segment_sentiments=[]
        for segment in text_segments:
            segment_sentiments.append(analyze_sentiment(segment, model_name, sentiment_map))
        segment_sentiments = [x for x in segment_sentiments if x != "-9"]

        if segment_sentiments:
            all_sentiments.append(majority_vote(segment_sentiments))

    if all_sentiments:
        return majority_vote(all_sentiments)
    else:
        return "0"

if __name__ == "__main__":
    sample_text = "The Bitcoin market is too volatile to trust." * 10
    print(predict_sentiment(sample_text))
