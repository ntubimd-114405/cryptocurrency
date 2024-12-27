import requests
import MySQLdb  # Use MySQLdb from mysqlclient instead of mysql.connector
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

# CoinMarketCap API 端點
def main(s):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {
        'start': str(s),  # 從第1名開始
        'limit': '500',  # 取得前 50 種幣
        'convert': 'USD'  # 以 USD 為基準貨幣
    }

    # 連接到 MariaDB 使用 MySQLdb (mysqlclient)
    conn = MySQLdb.connect(
        host="localhost",
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db="cryptocurrency",
        charset='utf8mb4',
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
        conversion_url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
        conversion_params = {
            'amount': 1,  # 換算 1 美元
            'id': 2781,  # USD 的 CoinMarketCap ID
            'convert': 'EUR'
        }
        conversion_response = requests.get(conversion_url, headers=headers, params=conversion_params)
        if conversion_response.status_code == 200:
            eur_conversion_rate = conversion_response.json()['data']['quote']['EUR']['price']

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

        # 準備一次性請求的幣種 ID 列表
        coin_ids = [str(coin["id"]) for coin in data]  # 擷取所有幣種的 ID

        # 使用 Coin IDs 一次性請求 logo 和其他資料
        info_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/info"
        info_params = {
            'id': ','.join(coin_ids)  # 將幣種 ID 組合成一個逗號分隔的字串
        }
        info_response = requests.get(info_url, headers=headers, params=info_params)
        
        if info_response.status_code == 200:
            info_data = info_response.json()['data']

            # 處理每個幣種的資料
            for coin in data:
                coin_name = coin["name"]  # 幣種名稱 (如 Bitcoin, Ethereum 等)
                coin_abbreviation = coin["symbol"]  # 幣種簡稱 (如 BTC, ETH 等)
                usd_price = float(coin["quote"]["USD"]["price"])  # 美元價格
                eur_price = usd_price * eur_conversion_rate  # 使用實時匯率換算成歐元
                twd_price = usd_price * twd_conversion_rate  # 使用實時匯率換算成台幣
                jpy_price = usd_price * jpy_conversion_rate  # 使用實時匯率換算成日元
                market_cap = float(coin["quote"]["USD"]["market_cap"])  # 市值
                volume_24h = float(coin["quote"]["USD"]["volume_24h"])  # 24小時交易量
                change_24h = float(coin["quote"]["USD"]["percent_change_24h"])  # 24小時變動百分比

                # 從 info_data 中提取 logo_url
                coin_id = str(coin["id"])
                logo_url = info_data.get(coin_id, {}).get('logo', '')  # 如果有 logo_url

                if not logo_url:
                    print(f"警告：{coin_name} ({coin_abbreviation}) 沒有 logo_url")

                # 檢查 Coin 資料表是否已經有該幣種（僅根據 api_id）
                cursor.execute("""SELECT id FROM main_coin WHERE api_id = %s""", (coin["id"],))
                coin_record = cursor.fetchone()

                # 若 Coin 資料表中沒有該幣種，則插入
                if not coin_record:
                    cursor.execute("INSERT INTO main_coin (coinname, abbreviation, logo_url, api_id) VALUES (%s, %s, %s, %s)", 
                                (coin_name, coin_abbreviation, logo_url, coin["id"]))  # 儲存 api_id
                    conn.commit()  # 提交事務
                    cursor.execute("""SELECT id FROM main_coin WHERE api_id = %s""", (coin["id"],))
                    coin_record = cursor.fetchone()

                # 取得該幣種的 id
                coin_id = coin_record[0]

                # 插入 BitcoinPrice 資料
                cursor.execute(insert_query, (coin_id, usd_price, twd_price, jpy_price, eur_price, market_cap, volume_24h, change_24h, timestamp))
                conn.commit()  # 提交事務
                print(f"數據已插入：{coin_name} ({coin_abbreviation}) - USD = {usd_price}, TWD = {twd_price}, JPY = {jpy_price}, EUR = {eur_price}, 時間 = {timestamp}")
        else:
            print("獲取 logo 資料失敗，狀態碼：", info_response.status_code)
    else:
        print("請求失敗，狀態碼：", response.status_code)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    start=[1]
    for i in start:
        main(i)
