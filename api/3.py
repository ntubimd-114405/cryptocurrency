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

# CryptoCompare API 端點
url = "https://min-api.cryptocompare.com/data/price"
coins = ['BTC', 'ETH', 'LTC', 'XRP', 'BCH', 'ADA', 'DOT', 'SOL', 'BNB', 'DOGE',
         'TRX', 'MATIC', 'AVAX', 'SHIB', 'LUNA', 'LINK', 'EOS', 'FIL', 'FTM', 'CRV']

# 連接到 MariaDB
conn = mysql.connector.connect(
    host="localhost",
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database="cryptocurrency",
    time_zone="+08:00"
)
cursor = conn.cursor()

# 插入數據的 SQL 查詢
insert_query = """
INSERT INTO main_bitcoinprice (coinname, usd, eur, timestamp)
VALUES (%s, %s, %s, %s)
"""

timestamp = datetime.now() - timedelta(hours=8)  # 當前時間戳

for coin in coins:
    params = {'fsym': coin, 'tsyms': 'USD,EUR'}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        usd_price = data.get('USD')
        eur_price = data.get('EUR')

        # 插入數據
        cursor.execute(insert_query, (coin, usd_price, eur_price, timestamp))
        conn.commit()
        print(f"數據已插入：{coin} - USD = {usd_price}, EUR = {eur_price}, 時間 = {timestamp}")
    else:
        print(f"{coin} 的請求失敗，狀態碼：{response.status_code}")

cursor.close()
conn.close()
