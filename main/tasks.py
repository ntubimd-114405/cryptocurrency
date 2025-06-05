import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptocurrency.settings')

from celery import shared_task
from datetime import datetime, timedelta
from dateutil import parser
from data_collector.coin_history.ccxt_price import CryptoHistoryFetcher

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
        latest_date = datetime(2020, 1, 1, 0, 0)
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

@shared_task
def fetch_history():
    from celery import group
    from .models import Coin
    from django.db.models import Q
    
    #coin_history = Coin.objects.all().order_by('id')[:3]
    coin_history = Coin.objects.filter(Q(id=34) | Q(id__lte=5)).order_by('id')
    tasks = group(fetch_coin_history.s(coin.id) for coin in coin_history)
    tasks.apply_async()


from api.coindata.all import main 
@shared_task
def crypto_data():
    main(1)