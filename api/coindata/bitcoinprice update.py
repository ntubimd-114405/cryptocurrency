import requests
import MySQLdb  # 使用 mysqlclient 的 MySQLdb 模組
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

def main():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {
        'start': '1',  # 起始位置
        'limit': '500',   # 每次請求最多 900 種幣
        'convert': 'USD'  # 使用美元作為基準貨幣
    }

    # 連接到 MariaDB 使用 mysqlclient 的 MySQLdb 模組
    conn = MySQLdb.connect(
        host="localhost",
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database="cryptocurrency",
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    # 插入數據的 SQL 查詢
    insert_query = """
    INSERT INTO main_bitcoinprice (coin_id, usd, twd, jpy, eur, market_cap, volume_24h, change_24h, timestamp)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    timestamp = datetime.now() - timedelta(hours=8)  # 當前時間戳

    # 獲取幣種列表
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()['data']
        
        # 獲取美元到歐元的匯率
        eur_conversion_url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
        eur_conversion_params = {
            'amount': 1,  # 換算 1 美元
            'id': 2781,  # USD 的 CoinMarketCap ID
            'convert': 'EUR'
        }
        eur_conversion_response = requests.get(eur_conversion_url, headers=headers, params=eur_conversion_params)
        if eur_conversion_response.status_code == 200:
            eur_conversion_rate = eur_conversion_response.json()['data']['quote']['EUR']['price']
        else:
            print("美元到歐元匯率請求失敗")
            return

        # 獲取美元到台幣的匯率
        twd_conversion_url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
        twd_conversion_params = {
            'amount': 1,  # 換算 1 美元
            'id': 2781,  # USD 的 CoinMarketCap ID
            'convert': 'TWD'
        }
        twd_conversion_response = requests.get(twd_conversion_url, headers=headers, params=twd_conversion_params)
        if twd_conversion_response.status_code == 200:
            twd_conversion_rate = twd_conversion_response.json()['data']['quote']['TWD']['price']
        else:
            print("美元到台幣匯率請求失敗")
            return
        
        # 獲取美元到日元的匯率
        jpy_conversion_url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
        jpy_conversion_params = {
            'amount': 1,  # 換算 1 美元
            'id': 2781,  # USD 的 CoinMarketCap ID
            'convert': 'JPY'
        }
        jpy_conversion_response = requests.get(jpy_conversion_url, headers=headers, params=jpy_conversion_params)
        if jpy_conversion_response.status_code == 200:
            jpy_conversion_rate = jpy_conversion_response.json()['data']['quote']['JPY']['price']
        else:
            print("美元到日元匯率請求失敗")
            return

        cursor.execute("""TRUNCATE TABLE main_bitcoinprice;""")
        conn.commit()

        # 處理每個幣種的資料
        for coin in data:
            usd_price = float(coin["quote"]["USD"]["price"])  # 美元價格
            eur_price = usd_price * eur_conversion_rate       # 歐元價格
            twd_price = usd_price * twd_conversion_rate       # 台幣價格
            jpy_price = usd_price * jpy_conversion_rate       # 日元價格
            market_cap = float(coin["quote"]["USD"]["market_cap"])  # 市值
            volume_24h = float(coin["quote"]["USD"]["volume_24h"])  # 24小時交易量
            change_24h = float(coin["quote"]["USD"]["percent_change_24h"])  # 24小時變動百分比

            # 根據 api_id 查找 coin_id
            cursor.execute("""SELECT id FROM main_coin WHERE api_id = %s""", (coin["id"],))
            coin_record = cursor.fetchone()

            if coin_record:
                coin_id = coin_record[0]  # 取得對應的 coin_id
                
                # 插入新資料
                cursor.execute(insert_query, (coin_id, usd_price, twd_price, jpy_price, eur_price, market_cap, volume_24h, change_24h, timestamp))
                conn.commit()
                print(f"更新成功：coin_id = {coin_id}, USD = {usd_price}, TWD = {twd_price}, JPY = {jpy_price}, EUR = {eur_price}, 市值 = {market_cap}, 24小時交易量 = {volume_24h}, 24小時變動 = {change_24h}, 時間 = {timestamp}")
            else:
                print(f"未找到對應的 coin_id，api_id = {coin['id']}")
    else:
        print("請求失敗，狀態碼：", response.status_code)

    cursor.close()
    conn.close()

main()
