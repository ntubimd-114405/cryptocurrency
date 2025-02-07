from celery import shared_task
from datetime import datetime, timedelta
import os
from .crawler.news import *
from data_collector.coin_history.ccxt_price import CryptoHistoryFetcher
from data_collector.new_scraper import site_all
from dateutil import parser

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptocurrency.settings')
@shared_task
def news_crawler():
    from .models import NewsWebsite,NewsArticle
    from django.db.models import Q

    websites=site_all.website()
    for site in websites:
        NewsWebsite.objects.update_or_create(
                url=site.url,
                defaults={
                "name":site.name,
                'icon_url': site.icon_url,
            },
            )
        website_instance = NewsWebsite.objects.get(name=site.name)
        
        for article in site.fetch_page():
            article_time = parser.parse(article["time"])

            # 計算一個月前的時間（與文章時間的時區對齊）
            one_month_ago = datetime.now(article_time.tzinfo) - timedelta(days=30)

            # 如果文章時間超過一個月，則跳過
            if article_time < one_month_ago:
                continue
            defaults = {
            'title': article["title"],
            'time': article["time"],
            'website': website_instance
            }

            # 如果 image_url 存在，加入到 defaults
            if article.get("image_url"):
                defaults['image_url'] = article["image_url"]

            NewsArticle.objects.update_or_create(
                url=article["url"],
                defaults=defaults,
            )
        
    articles_empty = NewsArticle.objects.filter(
        Q(content__isnull=True) | Q(content__exact="") | Q(image_url__isnull=True) | Q(image_url__exact="")
    )
    for article in articles_empty:
        a=site_all.article(article)
        if a:
            a.get_news_details()
            NewsArticle.objects.update_or_create(
                    url=a.url,
                    defaults={
                    'title': a.title,
                    'time': a.time,
                    'image_url':a.image_url,
                    "content":a.content,
                    'website':a.website
                },
                )
            print(a.title)



'''

@shared_task
def fetch_history():
    from django.db.models import Max
    from .models import Coin,CoinHistory
    from celery import group
    from django.db import transaction

    coin_history = Coin.objects.all().order_by('id')[:3]  # 取前3个币种
    
    for coin in coin_history:
        # 查找该 coin 的最新日期
        latest_history = CoinHistory.objects.filter(coin=coin).aggregate(latest_date=Max('date'))
        latest_date = latest_history['latest_date']
        
        # 若找不到最新日期，设置为 2023-01-01
        if latest_date is None:
            latest_date = datetime(2023, 1, 1, 0, 0)
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

                coin_history_data.append(CoinHistory(
                    coin=coin,
                    date=date,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume,
                ))

            # 批量插入数据，避免逐条插入造成性能问题
            with transaction.atomic():  # 确保数据库一致性
                CoinHistory.objects.bulk_create(coin_history_data)

            print(f"成功存入数据库 {len(data)} 筆：{c.coin} {data[-1][0]}")
        else:
            print(f"没有数据存入数据库：{c.coin} {c.starttime}")

'''

@shared_task
def fetch_coin_history(coin_id):
    from .models import Coin, CoinHistory
    from datetime import datetime, timedelta
    from django.db import transaction
    from django.db.models import Max

    coin = Coin.objects.get(id=coin_id)

    # 查找該 coin 的最新日期
    latest_history = CoinHistory.objects.filter(coin=coin).aggregate(latest_date=Max('date'))
    latest_date = latest_history['latest_date']
    
    if latest_date is None:
        latest_date = datetime(2023, 1, 1, 0, 0)
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

            coin_history_data.append(CoinHistory(
                coin=coin,
                date=date,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
            ))

        # 批量插入数据，避免逐条插入造成性能问题
        with transaction.atomic():  # 确保数据库一致性
            CoinHistory.objects.bulk_create(coin_history_data)

        print(f"成功存入数据库 {len(data)} 筆：{c.coin} {data[-1][0]}")
    else:
        print(f"没有数据存入数据库：{c.coin} {c.starttime}")

@shared_task
def fetch_history():
    from celery import group
    from .models import Coin
    coin_history = Coin.objects.all().order_by('id')[:3]
    tasks = group(fetch_coin_history.s(coin.id) for coin in coin_history)
    tasks.apply_async()
