import requests
import MySQLdb
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from pathlib import Path

# 載入 .env
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv('coinmarketcap_api')
headers = {
    'X-CMC_PRO_API_KEY': api_key,
    'Accept': 'application/json'
}

def update_prices():
    print("🚀 開始更新前 500 幣種價格（每幣僅保留一筆紀錄）...")

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {
        'start': '1',
        'limit': '500',
        'convert': 'USD'
    }

    conn = MySQLdb.connect(
        host="localhost",
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db="cryptocurrency",
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("❌ 無法取得幣價資料：", response.status_code)
        return

    data = response.json()['data']
    timestamp = datetime.now() - timedelta(hours=8)

    # 匯率換算
    def get_rate(to_currency):
        rate_url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
        r = requests.get(rate_url, headers=headers, params={'amount': 1, 'id': 2781, 'convert': to_currency})
        return r.json()['data']['quote'][to_currency]['price'] if r.status_code == 200 else None

    twd_rate = get_rate("TWD")
    jpy_rate = get_rate("JPY")
    eur_rate = get_rate("EUR")

    insert_sql = """
        INSERT INTO main_bitcoinprice 
        (coin_id, usd, twd, jpy, eur, market_cap, volume_24h, change_24h, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    update_sql = """
        UPDATE main_bitcoinprice
        SET usd=%s, twd=%s, jpy=%s, eur=%s, market_cap=%s, volume_24h=%s, change_24h=%s, timestamp=%s
        WHERE coin_id=%s
    """

    for coin in data:
        api_id = coin["id"]
        usd = float(coin["quote"]["USD"]["price"])
        twd = usd * twd_rate
        jpy = usd * jpy_rate
        eur = usd * eur_rate
        market_cap = float(coin["quote"]["USD"]["market_cap"])
        volume_24h = float(coin["quote"]["USD"]["volume_24h"])
        change_24h = float(coin["quote"]["USD"]["percent_change_24h"])

        # 取得 coin_id
        cursor.execute("SELECT id FROM main_coin WHERE api_id = %s", (api_id,))
        result = cursor.fetchone()
        if not result:
            print(f"⚠️ 找不到 api_id={api_id} 的幣種，跳過")
            continue

        coin_id = result[0]

        # 檢查是否已經有這筆紀錄
        cursor.execute("SELECT id FROM main_bitcoinprice WHERE coin_id = %s", (coin_id,))
        existing = cursor.fetchone()

        if existing:
            # 已存在，執行 UPDATE
            cursor.execute(update_sql, (usd, twd, jpy, eur, market_cap, volume_24h, change_24h, timestamp, coin_id))
            print(f"✅ 更新：{coin['name']} ({coin['symbol']}) - USD: {usd:.2f}")
        else:
            # 不存在，執行 INSERT
            cursor.execute(insert_sql, (coin_id, usd, twd, jpy, eur, market_cap, volume_24h, change_24h, timestamp))
            print(f"✅ 新增：{coin['name']} ({coin['symbol']}) - USD: {usd:.2f}")

    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 幣價更新完成（每幣保留一筆最新紀錄）")

if __name__ == "__main__":
    update_prices()
