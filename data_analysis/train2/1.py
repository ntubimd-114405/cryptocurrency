import requests


def download_file(url,name):
    r1 = requests.get(url)
    if r1.status_code == 200:
        with open(f"{name}", "wb") as f:
            f.write(r1.content)


def prediction_api(model_id,feature):
    # 你的 Ngrok 公開網址，請替換為你自己的
    API_URL = "https://927c-34-148-232-255.ngrok-free.app/generate_csv"

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
        download_file(result.get("url1"),f"{model_id}_pred.csv")
        download_file(result.get("url2"),f"{model_id}_model.h5")
    else:
        print("❌ 發送失敗，狀態碼：", response.status_code)
        print("內容：", response.text)

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