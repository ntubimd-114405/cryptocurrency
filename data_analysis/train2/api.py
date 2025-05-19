import requests
from pathlib import Path
import os
from dotenv import load_dotenv

def download_file(url,name,save_path):
    r1 = requests.get(url)
    os.makedirs(save_path, exist_ok=True) 
    full_path = os.path.join(save_path, name)
    if r1.status_code == 200:
        with open(full_path, "wb") as f:
            f.write(r1.content)

def prediction_api(model_id,feature):
    env_path = Path(__file__).resolve().parents[2] / '.env'  # 上兩層目錄
    load_dotenv(dotenv_path=env_path)
    API_URL = os.getenv('API_URL')+'/generate_csv'


    # 要傳送的資料
    data = {
        "model_id": model_id,
        "feature": feature
    }

    # 發送 POST 請求
    response = requests.post(API_URL, json=data)

    # 顯示結果
    if response.status_code == 200:
        result = response.json()
        print(result)
        download_file(result.get("url1"),f"model.h5",f"media/model/{model_id}/")
        download_file(result.get("url2"),f"pred.csv",f"media/model/{model_id}/")
        download_file(result.get("url3"),f"evaluation_metrics.csv",f"media/model/{model_id}/")
    else:
        print("❌ 發送失敗，狀態碼：", response.status_code)
        print("內容：", response.text)

if __name__ == "__main__":
    features = [
                'close_price', 
                'S&P 500 Index', 
                'VIX Volatility Index', 
                'WTI Crude Oil Futures', 
                'US Dollar Index', 
                'Gold Futures', 
                'volume', 
                'positive', 
                'neutral', 
                'negative', 
                'Average Block Size', 
                'Difficulty', 
                'Hash Rate', 
                'Miners Revenue', 
                'Number Of Unique Addresses Used', 
                'open_price', 
                'high_price', 
                'low_price'
    ]
    prediction_api("hello2",features)