import requests
import MySQLdb
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from pathlib import Path

# 讀取 .env 設定
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv('coinmarketcap_api')
headers = {
    'X-CMC_PRO_API_KEY': api_key,
    'Accept': 'application/json'
}

# 🔧 插入或更新幣種資料
def update_or_insert_coin(cursor, conn, coin, logo_url):
    coin_id_api = coin["id"]
    name = coin["name"]
    symbol = coin["symbol"]

    cursor.execute("SELECT id FROM main_coin WHERE api_id = %s", (coin_id_api,))
    result = cursor.fetchone()

    if result:
        # ✅ 更新
        cursor.execute(
            """
            UPDATE main_coin 
            SET coinname = %s, abbreviation = %s, logo_url = %s 
            WHERE api_id = %s
            """,
            (name, symbol, logo_url, coin_id_api)
        )
        conn.commit()
        print(f"✅ 更新：{name} ({symbol})")
        return result[0]
    else:
        # ✅ 新增
        cursor.execute(
            """
            INSERT INTO main_coin (coinname, abbreviation, logo_url, api_id)
            VALUES (%s, %s, %s, %s)
            """,
            (name, symbol, logo_url, coin_id_api)
        )
        conn.commit()
        print(f"✅ 新增：{name} ({symbol})")
        return cursor.lastrowid

def main(start):
    conn = MySQLdb.connect(
        host="localhost",
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db="cryptocurrency",
        charset='utf8mb4',
    )
    cursor = conn.cursor()

    print("🚀 開始抓取幣種資料 ...")
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {
        'start': str(start),
        'limit': '500',
        'convert': 'USD'
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("❌ 幣種列表 API 請求失敗:", response.status_code)
        return

    data = response.json()['data']

    def get_rate(to_currency):
        r = requests.get(
            "https://pro-api.coinmarketcap.com/v1/tools/price-conversion",
            headers=headers,
            params={'amount': 1, 'id': 2781, 'convert': to_currency}
        )
        return r.json()['data']['quote'][to_currency]['price'] if r.status_code == 200 else 0

    eur_rate = get_rate("EUR")
    twd_rate = get_rate("TWD")
    jpy_rate = get_rate("JPY")

    # 抓所有幣 logo
    coin_ids = [str(coin["id"]) for coin in data]
    info_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/info"
    info_response = requests.get(info_url, headers=headers, params={'id': ','.join(coin_ids)})
    info_data = info_response.json().get("data", {}) if info_response.status_code == 200 else {}

    update_sql = """
        UPDATE main_bitcoinprice
        SET usd=%s, twd=%s, jpy=%s, eur=%s, market_cap=%s, volume_24h=%s, change_24h=%s, timestamp=%s
        WHERE coin_id=%s
    """
    insert_sql = """
        INSERT INTO main_bitcoinprice 
        (coin_id, usd, twd, jpy, eur, market_cap, volume_24h, change_24h, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    timestamp = datetime.now() - timedelta(hours=8)

    for coin in data:
        coin_id_api = coin["id"]
        usd = float(coin["quote"]["USD"]["price"])
        twd = usd * twd_rate
        jpy = usd * jpy_rate
        eur = usd * eur_rate
        market_cap = float(coin["quote"]["USD"]["market_cap"])
        volume_24h = float(coin["quote"]["USD"]["volume_24h"])
        change_24h = float(coin["quote"]["USD"]["percent_change_24h"])
        logo_url = info_data.get(str(coin_id_api), {}).get("logo", "")

        # 更新或新增 main_coin
        coin_id = update_or_insert_coin(cursor, conn, coin, logo_url)

        # 更新或插入價格
        cursor.execute("SELECT id FROM main_bitcoinprice WHERE coin_id = %s", (coin_id,))
        price_exists = cursor.fetchone()

        if price_exists:
            cursor.execute(update_sql, (
                usd, twd, jpy, eur, market_cap, volume_24h, change_24h, timestamp, coin_id
            ))
            print(f"🔁 更新價格：{coin['name']} ({coin['symbol']}) - USD: {usd:.2f}")
        else:
            cursor.execute(insert_sql, (
                coin_id, usd, twd, jpy, eur, market_cap, volume_24h, change_24h, timestamp
            ))
            print(f"🆕 新增價格：{coin['name']} ({coin['symbol']}) - USD: {usd:.2f}")

        conn.commit()

    cursor.close()
    conn.close()
    print("🎉 所有幣種與價格更新完成")

if __name__ == "__main__":
    main(1)
