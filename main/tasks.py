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

@shared_task
def fetch_coin_history(coin_id):
    from .models import Coin, CoinHistory
    from django.db import transaction
    from django.db.models import Max
    

    coin = Coin.objects.get(id=coin_id)

    # 查找該 coin 的最新日期
    latest_history = CoinHistory.objects.filter(coin=coin).aggregate(latest_date=Max('date'))
    latest_date = latest_history['latest_date']
    
    if latest_date is None:
        latest_date = datetime(2024, 1, 1, 0, 0)
    else:
        latest_date = latest_date + timedelta(minutes=1)

    # 获取历史数据
    c = CryptoHistoryFetcher(coin.abbreviation, latest_date)
    data = c.get_history()

    # 如果数据不为空，批量保存
    if data:
        coin_history_data = []
        for history_data in data:
            date = datetime.strptime(history_data[0], '%Y-%m-%d %H:%M:%S')
            date = str(date) + "+00:00"
            open_price, high_price, low_price, close_price, volume = history_data[1:6]

            CoinHistory.objects.get_or_create(
                coin=coin,
                date=date,
                defaults={
                    "open_price": open_price,
                    "high_price": high_price,
                    "low_price": low_price,
                    "close_price": close_price,
                    "volume": volume,
                }
            )
        print(f"成功存入数据库 {len(data)} 筆：{c.coin} {data[-1][0]}")
    else:
        print(f"没有数据存入数据库：{c.coin} {c.starttime}")

# @shared_task
# def fetch_coin_history(coin_id):
#     from .models import Coin, CoinHistory
#     from django.db.models import Max
#     from datetime import datetime, timedelta

#     # 取得 coin
#     coin = Coin.objects.get(id=coin_id)

#     # 查找該 coin 的最新日期
#     latest_history = CoinHistory.objects.filter(coin=coin).aggregate(latest_date=Max('date'))
#     latest_date = latest_history['latest_date']

#     if latest_date is None:
#         # 沒有任何歷史資料，從固定時間開始
#         latest_date = datetime(2024, 1, 1)
#     else:
#         # 往後一天
#         latest_date = latest_date + timedelta(days=1)

#     # 取得歷史數據（假設 CryptoHistoryFetcher 可以指定日線資料）
#     c = CryptoHistoryFetcher(coin.abbreviation, latest_date)  # 加 interval 參數，確保是日線
#     data = c.get_history()

#     if data:
#         count_new = 0
#         for history_data in data:
#             # 解析日期（只取日期，不帶時間）
#             date = pd.to_datetime(history_data[0]).date()
            
#             open_price, high_price, low_price, close_price, volume = history_data[1:6]

#             # 判斷是否已存在，若不存在才新增
#             obj, created = CoinHistory.objects.get_or_create(
#                 coin=coin,
#                 date=date,
#                 defaults={
#                     "open_price": open_price,
#                     "high_price": high_price,
#                     "low_price": low_price,
#                     "close_price": close_price,
#                     "volume": volume,
#                 }
#             )
#             if created:
#                 count_new += 1

#         print(f"成功存入数据库 {count_new} 筆：{c.coin} 最新日期 {data[-1][0]}")
#     else:
#         print(f"没有数据存入数据库：{c.coin} {c.starttime}")

@shared_task
def fetch_history():
    from celery import group
    from .models import Coin
    from django.db.models import Q
    
    coin_history = Coin.objects.all().order_by('id')[:10]
    #coin_history = Coin.objects.filter(Q(id=34) | Q(id__lte=5)).order_by('id')
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

@shared_task
def fetch_and_store_coin_data():
    import requests 
    from datetime import datetime, timedelta  
    from main.models import Coin, BitcoinPrice
    from django.db import transaction
    api_key = os.getenv('coinmarketcap_api')
    headers = {
        'X-CMC_PRO_API_KEY': api_key,
        'Accept': 'application/json'
    }

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

        # 使用 Coin IDs 一次性請求 logo 和其他資料
        coin_ids = [str(coin["id"]) for coin in data]
        info_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/info"
        info_params = {
            'id': ','.join(coin_ids)  # 將幣種 ID 組合成一個逗號分隔的字串
        }
        info_response = requests.get(info_url, headers=headers, params=info_params)
        
        if info_response.status_code == 200:
            info_data = info_response.json()['data']
            timestamp = datetime.now() - timedelta(hours=8)  # 當前時間戳

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

                    # 插入 BitcoinPrice
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
            print("獲取 logo 資料失敗，狀態碼：", info_response.status_code)
    else:
        print("請求失敗，狀態碼：", response.status_code)

