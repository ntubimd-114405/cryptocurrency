import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptocurrency.settings')

from celery import shared_task
from datetime import datetime, timedelta
from dateutil import parser
from data_collector.coin_history.ccxt_price import CryptoHistoryFetcher
import pandas as pd
from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

# 3-2取得指定幣種歷史數據任務函數細節編輯器
@shared_task
def fetch_coin_history(coin_id):
    from .models import Coin, CoinHistory
    from django.db.models import Max
    from django.db import transaction

    coin = Coin.objects.get(id=coin_id)

    # 查找該 coin 的最新日期
    latest_history = CoinHistory.objects.filter(coin=coin).aggregate(latest_date=Max('date'))
    latest_date = latest_history['latest_date']
    
    if latest_date is None:
        latest_date = datetime(2025, 4, 17, 0, 0)
    else:
        latest_date = latest_date + timedelta(minutes=1)
# 3-3 CryptoHistoryFetcher類別ccxt抓取部分
    c = CryptoHistoryFetcher(coin.abbreviation, latest_date)
    data = c.get_history()

# 3-4 取得數據格式轉換與資料庫存儲部分
    if data:
        # 先把資料轉成要插入的物件
        objs = []
        dates_to_insert = set()

        for history_data in data:
            date = datetime.strptime(history_data[0], '%Y-%m-%d %H:%M:%S')
            date = str(date) + "+00:00"
            open_price, high_price, low_price, close_price, volume = history_data[1:6]

            # 避免同一批次資料重複
            if date in dates_to_insert:
                continue
            dates_to_insert.add(date)

            objs.append(
                CoinHistory(
                    coin=coin,
                    date=date,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume
                )
            )

        # 只查詢已有的資料日期
        existing_dates = set(
            CoinHistory.objects.filter(coin=coin, date__in=dates_to_insert)
            .values_list('date', flat=True)
        )

        # 過濾已存在的日期
        objs_to_create = [obj for obj in objs if obj.date not in existing_dates]

        if objs_to_create:
            with transaction.atomic():
                CoinHistory.objects.bulk_create(objs_to_create)
            print(f"成功存入資料庫 {len(objs_to_create)} 筆：{c.coin} {data[-1][0]}")
        else:
            print(f"資料已存在，無新資料存入：{c.coin} {data[-1][0]}")

    else:
        print(f"沒有資料存入資料庫：{c.coin} {c.starttime}")

def fetch_all_coins_history_1day():
    from .models import Coin, CoinHistory
    from django.db.models import Max
    from django.db import transaction
    # 排除 id 1~10 的幣種
    coins = Coin.objects.exclude(id__in=range(1, 11))

    for coin in coins:
        print(f"正在處理 {coin.abbreviation} (id={coin.id})...")

        latest_history = CoinHistory.objects.filter(coin=coin).aggregate(latest_date=Max('date'))
        latest_date = latest_history['latest_date']

        if latest_date is None:
            latest_date = datetime(2025, 4, 17, 0, 0)
        else:
            latest_date = latest_date + timedelta(minutes=1)

        c = CryptoHistoryFetcher(coin.abbreviation, latest_date,"1d")
        data = c.get_history()

        if not data:
            print(f"⚠️ 沒有資料存入資料庫：{c.coin} {c.starttime}")
            continue

        objs = []
        dates_to_insert = set()

        for history_data in data:
            date = datetime.strptime(history_data[0], '%Y-%m-%d %H:%M:%S')
            date_str = str(date) + "+00:00"
            open_price, high_price, low_price, close_price, volume = history_data[1:6]

            if date_str in dates_to_insert:
                continue
            dates_to_insert.add(date_str)

            objs.append(
                CoinHistory(
                    coin=coin,
                    date=date_str,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume
                )
            )

        # 查詢資料庫中已存在的日期，避免重複插入
        existing_dates = set(
            CoinHistory.objects.filter(coin=coin, date__in=dates_to_insert)
            .values_list('date', flat=True)
        )

        objs_to_create = [obj for obj in objs if obj.date not in existing_dates]

        if objs_to_create:
            with transaction.atomic():
                CoinHistory.objects.bulk_create(objs_to_create)
            print(f"✅ 成功存入資料庫 {len(objs_to_create)} 筆：{c.coin} {data[-1][0]}")
        else:
            print(f"ℹ️ 資料已存在，無新資料存入：{c.coin} {data[-1][0]}")

    print("🎯 所有幣種歷史資料更新完成！")

# 3-1 Celery任務調度程式碼編輯器介面
@shared_task
def fetch_history():
    from celery import group
    from .models import Coin
    from django.db.models import Q
    
    coin_history = Coin.objects.all().order_by('id')[:10]
    tasks = group(fetch_coin_history.s(coin.id) for coin in coin_history)
    tasks.apply_async()


def get_conversion_rates(headers):
    import requests 
    rates = {}
    currencies = ['EUR', 'TWD', 'JPY']
    for currency in currencies:
        conversion_url = f"https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
        conversion_params = {
            'amount': 1,  # 換算 1 美元
            'id': 2781,  # USD 的 CoinMarketCap ID
            'convert': currency
        }
        conversion_response = requests.get(conversion_url, headers=headers, params=conversion_params)
        if conversion_response.status_code == 200:
            rates[currency.lower()] = conversion_response.json()['data']['quote'][currency]['price']
    return rates

# 2-1「抓取並儲存加密貨幣行情資料」
@shared_task
def fetch_and_store_coin_data():
    import requests 
    from datetime import datetime, timedelta  
    from main.models import Coin, BitcoinPrice
    from django.db import transaction
    from django.utils import timezone
    api_key = os.getenv('coinmarketcap_api')
    headers = {
        'X-CMC_PRO_API_KEY': api_key,
        'Accept': 'application/json'
    }
#2-2「取得加密貨幣列表及匯率資料」
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {
        'start': '1',  # 從第1名開始
        'limit': '500',  # 取得前 500 種幣
        'convert': 'USD'  # 以 USD 為基準貨幣
    }

    # 獲取幣種列表
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()['data']
        
        # 獲取美元到其他貨幣的匯率
        conversion_rates = get_conversion_rates(headers)

#2-3「批量取得幣種logo與資訊」
        # 使用 Coin IDs 一次性請求 logo 和其他資料
        coin_ids = [str(coin["id"]) for coin in data]
        info_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/info"
        info_params = {
            'id': ','.join(coin_ids)  # 將幣種 ID 組合成一個逗號分隔的字串
        }
        info_response = requests.get(info_url, headers=headers, params=info_params)
        
        if info_response.status_code == 200:
            info_data = info_response.json()['data']
            timestamp = timezone.now()  # 取得當前帶時區的 UTC 時間

#2-4「資料庫新增或更新操作」
            # 使用 Django ORM 進行資料插入
            with transaction.atomic():
                for coin in data:
                    coin_name = coin["name"]
                    coin_abbreviation = coin["symbol"]
                    usd_price = float(coin["quote"]["USD"]["price"])
                    eur_price = usd_price * conversion_rates['eur']
                    twd_price = usd_price * conversion_rates['twd']
                    jpy_price = usd_price * conversion_rates['jpy']
                    market_cap = float(coin["quote"]["USD"]["market_cap"])
                    volume_24h = float(coin["quote"]["USD"]["volume_24h"])
                    change_24h = float(coin["quote"]["USD"]["percent_change_24h"])

                    logo_url = info_data.get(str(coin["id"]), {}).get('logo', '')

                    # 確認 Coin 是否存在
                    coin_record, created = Coin.objects.get_or_create(
                        api_id=coin["id"],
                        defaults={'coinname': coin_name, 'abbreviation': coin_abbreviation, 'logo_url': logo_url}
                    )
                    # 先嘗試取得該 coin 現有資料
                    obj = BitcoinPrice.objects.filter(coin=coin_record).first()

                    if obj:
                        # 更新現有資料
                        obj.usd = usd_price
                        obj.twd = twd_price
                        obj.jpy = jpy_price
                        obj.eur = eur_price
                        obj.market_cap = market_cap
                        obj.volume_24h = volume_24h
                        obj.change_24h = change_24h
                        obj.timestamp = timestamp  # 更新成當前時間
                        obj.save()
                    else:
                        # 沒有資料則新增
                        BitcoinPrice.objects.create(
                            coin=coin_record,
                            usd=usd_price,
                            twd=twd_price,
                            jpy=jpy_price,
                            eur=eur_price,
                            market_cap=market_cap,
                            volume_24h=volume_24h,
                            change_24h=change_24h,
                            timestamp=timestamp
                        )
                    print(f"數據已插入：{coin_name} ({coin_abbreviation}) - USD = {usd_price}, TWD = {twd_price}, JPY = {jpy_price}, EUR = {eur_price}, 時間 = {timestamp}")
        else:

#2-5「日誌輸出與錯誤提示」
            print("獲取 logo 資料失敗，狀態碼：", info_response.status_code)
    else:
        print("請求失敗，狀態碼：", response.status_code)

