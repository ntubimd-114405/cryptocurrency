import requests
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from pathlib import Path

# 設定 .env 檔案的路徑
env_path = Path(__file__).resolve().parents[2] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

# CoinMarketCap API 金鑰
api_key = os.getenv('coinmarketcap_api')
headers = {
    'X-CMC_PRO_API_KEY': api_key,
    'Accept': 'application/json'
}

# API 端點
url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"

# 定義轉換參數
def convert_currency(amount, from_currency_id, to_currency):
    params = {
        "amount": amount,          # 要轉換的金額
        "id": from_currency_id,    # 原始貨幣的 CoinMarketCap ID
        "convert": to_currency     # 目標貨幣代碼
    }

# 資料庫連線設置
conn = mysql.connector.connect(
    host="localhost",
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database="cryptocurrency",
    time_zone="+08:00"
)

cursor = conn.cursor()

insert_query = """
INSERT INTO main_cryptodata (coin_id, price_usd, price_twd, price_eur, market_cap, volume_24h, change_24h, fetched_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

timestamp = datetime.now() - timedelta(hours=8)  # 當前時間戳

def fetch_latest_crypto_data():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {
        "start": "1",
        "limit": "50",
        "convert": "USD"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"API 請求失敗，狀態碼: {response.status_code}")
        return None

# 轉換貨幣價格
def convert_currency(amount, from_currency_id, to_currency):
    url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
    params = {
        "amount": amount,
        "id": from_currency_id,  # USD 的 CoinMarketCap ID 是 2781
        "convert": to_currency
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()["data"]["quote"][to_currency]["price"]
    else:
        print(f"匯率轉換失敗，狀態碼: {response.status_code}")
        return None

# 主邏輯
def main():
    crypto_data = fetch_latest_crypto_data()
    error_list=[]
    if crypto_data:
        usd_to_twd = convert_currency(1, 2781, "TWD")  # 1 USD -> TWD
        usd_to_eur = convert_currency(1, 2781, "EUR")  # 1 USD -> EUR

        for coin in crypto_data:
            coin_name = coin["name"]
            price_usd = coin["quote"]["USD"]["price"]
            market_cap = coin["quote"]["USD"]["market_cap"]
            volume_24h = coin["quote"]["USD"]["volume_24h"]
            change_24h = coin["quote"]["USD"]["percent_change_24h"]

            # 檢查 Coin 是否存在於資料庫
            cursor.execute("SELECT id FROM main_coin WHERE coinname = %s", (coin_name,))
            coin_record = cursor.fetchone()

            if coin_record:
                coin_id = coin_record[0]  # 取出查詢到的 Coin ID

                # 進行匯率轉換
                price_twd = price_usd * usd_to_twd
                price_eur = price_usd * usd_to_eur

                # 當前時間戳
                fetched_at = datetime.now() - timedelta(hours=8)

                # 插入數據到 CryptoData 表
                cursor.execute(
                    insert_query,
                    (coin_id, price_usd, price_twd, price_eur, market_cap, volume_24h, change_24h, fetched_at),
                )
                conn.commit()
                print(f"已插入資料: {coin_name}, USD: {price_usd}, TWD: {price_twd}, EUR: {price_eur}")
            else:
                error_list.append(coin_name)
                print(f"Coin 不存在於資料庫中，跳過: {coin_name}")
    print(error_list)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()