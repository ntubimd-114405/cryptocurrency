import requests
import mysql.connector
from datetime import datetime,timedelta
from dotenv import load_dotenv
import os
from pathlib import Path

# 設定 .env 檔案的路徑
env_path = Path(__file__).resolve().parents[2] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)



# CryptoCompare API 端點
url = "https://min-api.cryptocompare.com/data/price"
params = {
    'fsym': 'BTC',  # 比特幣
    'tsyms': 'USD,EUR'  # 查詢美元和歐元價格
}

# 發送 GET 請求
response = requests.get(url, params=params)

# 檢查請求是否成功
if response.status_code == 200:
    data = response.json()  # 解析 JSON 資料
    usd_price = data.get('USD')
    eur_price = data.get('EUR')
    timestamp = datetime.now()- timedelta(hours=8) # 當前時間戳
    # 連接到 MariaDB
    conn = mysql.connector.connect(
        host="localhost",  # 替換為你的 MariaDB 主機地址
        user=os.getenv('DB_USER'),  # 替換為你的用戶名
        password=os.getenv('DB_PASSWORD'),  # 替換為你的密碼
        database="cryptocurrency",  # 替換為你的資料庫名稱
        time_zone="+08:00"  # 設定為台灣時間
    )

    cursor = conn.cursor()

    # 插入數據
    insert_query = """
    INSERT INTO main_bitcoinprice (usd, eur, timestamp)
    VALUES (%s, %s, %s)
    """
    cursor.execute(insert_query, (usd_price, eur_price, timestamp))
    conn.commit()  # 提交事務

    print(f"數據已插入：USD = {usd_price}, EUR = {eur_price}, 時間 = {timestamp}")

    cursor.close()
    conn.close()

else:
    print("請求失敗", response.status_code)
