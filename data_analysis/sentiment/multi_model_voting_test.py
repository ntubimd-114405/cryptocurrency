import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 只顯示錯誤

import pandas as pd
from transformers import pipeline
from collections import Counter
import tensorflow as tf
import logging
import torch

tf.debugging.set_log_device_placement(False)
tf.get_logger().setLevel('ERROR')
logging.getLogger("transformers").setLevel(logging.ERROR)

# ✅ 修改為 Kaggle 訓練好的本地模型
LOCAL_MODEL_PATH = "./models/crypto_sentiment_model"

def analyze_sentiment(text, sentiment_map, max_length=512):
    device = 0 if torch.cuda.is_available() else -1  # 優先使用 GPU
    torch.cuda.set_device(device)  # 設定 CUDA 裝置

    # 使用本地模型
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model=LOCAL_MODEL_PATH,
        tokenizer=LOCAL_MODEL_PATH,
        device=device
    )

    result = sentiment_pipeline(text, truncation=True, max_length=max_length)[0]
    label = result['label']
    score = result['score']
    sentiment_number = sentiment_map.get(label, '0')  # 預設為 '0'

    if score <= 0.8:
        sentiment_number = "-9"  # 低於信心門檻
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
    sentiment_map = {"Bearish": "-1", "Neutral": "0", "Bullish": "1"}  # 你的標籤對應

    text_segments = split_text(text)  # 拆分長文本
    segment_sentiments = []
    
    for segment in text_segments:
        segment_sentiments.append(analyze_sentiment(segment, sentiment_map))

    segment_sentiments = [x for x in segment_sentiments if x != "-9"]  # 移除不確定的標籤

    if segment_sentiments:
        return majority_vote(segment_sentiments)
    else:
        return "0"

if __name__ == "__main__":
    sample_text = "The Bitcoin market is too volatile to trust." * 10
    print(predict_sentiment(sample_text))
