import requests
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from pathlib import Path

# 設定 .env 檔案的路徑
env_path = Path(__file__).resolve().parents[3] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

# CoinMarketCap API 金鑰
api_key = os.getenv('coinmarketcap_api')
headers = {
    'X-CMC_PRO_API_KEY': api_key,
    'Accept': 'application/json'
}

def main():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    # 連接到 MariaDB
    conn = mysql.connector.connect(
        host="localhost",
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database="cryptocurrency",
        time_zone="+08:00",
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    # 插入數據的 SQL 查詢
    insert_query = """
    INSERT INTO main_bitcoinprice (coin_id, usd, twd, jpy, eur, market_cap, volume_24h, change_24h, timestamp)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    timestamp = datetime.now() - timedelta(hours=8)  # 當前時間戳

    # 從 main_coin 表中獲取所有的 api_id
    cursor.execute("SELECT id, api_id FROM main_coin")
    coin_records = cursor.fetchall()
    
    if not coin_records:
        print("main_coin 表中沒有可用的 api_id")
        return

    # 準備請求幣種的數據
    coin_id_map = {record[1]: record[0] for record in coin_records}  # api_id 映射到 coin_id
    api_ids = ",".join(map(str, coin_id_map.keys()))  # 將 api_id 拼接為逗號分隔的字符串

    params = {
        'id': api_ids,  # 指定要查詢的 api_id
        'convert': 'USD'  # 使用美元作為基準貨幣
    }

    # 發送請求
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()['data']

        # 獲取匯率
        def get_conversion_rate(target_currency):
            conversion_url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
            conversion_params = {
                'amount': 1,
                'id': 2781,  # USD 的 CoinMarketCap ID
                'convert': target_currency
            }
            conversion_response = requests.get(conversion_url, headers=headers, params=conversion_params)
            if conversion_response.status_code == 200:
                return conversion_response.json()['data']['quote'][target_currency]['price']
            else:
                print(f"美元到 {target_currency} 匯率請求失敗")
                return None

        eur_conversion_rate = get_conversion_rate('EUR')
        twd_conversion_rate = get_conversion_rate('TWD')
        jpy_conversion_rate = get_conversion_rate('JPY')

        if not (eur_conversion_rate and twd_conversion_rate and jpy_conversion_rate):
            print("無法獲取所有匯率，退出程序")
            return

        cursor.execute("TRUNCATE TABLE main_bitcoinprice;")
        conn.commit()

        # 處理每個幣種的資料
        for api_id, coin_data in data.items():
            coin_id = coin_id_map.get(int(api_id))
            if not coin_id:
                print(f"未找到對應的 coin_id，api_id = {api_id}")
                continue

            usd_price = float(coin_data["quote"]["USD"]["price"])
            eur_price = usd_price * eur_conversion_rate
            twd_price = usd_price * twd_conversion_rate
            jpy_price = usd_price * jpy_conversion_rate
            market_cap = float(coin_data["quote"]["USD"].get("market_cap", 0))
            volume_24h = float(coin_data["quote"]["USD"].get("volume_24h", 0))
            change_24h = float(coin_data["quote"]["USD"].get("percent_change_24h", 0))

            # 插入新資料
            cursor.execute(insert_query, (coin_id, usd_price, twd_price, jpy_price, eur_price, market_cap, volume_24h, change_24h, timestamp))
            conn.commit()
            print(f"更新成功：coin_id = {coin_id}, USD = {usd_price}, TWD = {twd_price}, JPY = {jpy_price}, EUR = {eur_price}, 市值 = {market_cap}, 24小時交易量 = {volume_24h}, 24小時變動 = {change_24h}, 時間 = {timestamp}")
    else:
        print("請求失敗，狀態碼：", response.status_code)

    cursor.close()
    conn.close()

main()
