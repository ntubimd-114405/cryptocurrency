import os
import requests
from pathlib import Path
from dotenv import load_dotenv

def predict_sentiment_api(texts):
    # 取得 .env 路徑
    env_path = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(dotenv_path=env_path)
    
    API_URL = os.getenv('API_URL') + '/sentiment'

    data = {
        "texts": [
            texts
        ]
    }
    response = requests.post(API_URL, json=data)
    if response.status_code == 200:
        results = response.json()
        for item in results:
            print(f"文字: {item['text']}, 情感: {item['sentiment']}")
        return results[0]['sentiment']

if __name__ == "__main__":
    test_texts = [
    "The Bitcoin market is too volatile to trust." * 10,
    "Ethereum just surged after BlackRock announced their support.",
    "The crypto industry is facing increasing regulations and uncertainty."
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"\n[Sample {i}]")
        result = predict_sentiment_api(text)
        print("Predicted sentiment:", result)
