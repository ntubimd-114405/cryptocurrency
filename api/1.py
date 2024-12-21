import requests
import datetime

# CoinGecko API 端點
url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"


# 參數設定（指定貨幣，對美元，時間範圍為 7 天）
params = {
    'vs_currency': 'usd',  # 將價格轉換為美元
    'days': '7'            # 查詢最近 7 天的數據
}

# 發送 GET 請求
response = requests.get(url, params=params)
#https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=7

# 檢查請求是否成功
if response.status_code == 200:
    data = response.json()  # 解析 JSON 資料
    # 提取價格數據
    prices = data['prices']  # 格式: [[timestamp, price], ...]
    
    # 轉換為日期和價格列表
    for price_data in prices:
        timestamp = price_data[0]
        price = price_data[1]
        
        # 將時間戳轉換為日期
        date = datetime.datetime.fromtimestamp(timestamp / 1000)
        
        # 列印日期和價格
        print(f"日期: {date.strftime('%Y-%m-%d %H:%M:%S')} | 比特幣價格: ${price:.2f}")
else:
    print("請求失敗", response.status_code)