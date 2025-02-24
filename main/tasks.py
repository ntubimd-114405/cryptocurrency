import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptocurrency.settings')

from celery import shared_task
from datetime import datetime, timedelta
from dateutil import parser
from data_collector.coin_history.ccxt_price import CryptoHistoryFetcher

@shared_task
def news_crawler():
    from .models import NewsWebsite,NewsArticle
    from django.db.models import Q
    from data_collector.new_scraper import site_all

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

@shared_task
def news_sentiment():
    from .models import NewsArticle
    from data_analysis.sentiment.multi_model_voting import predict_sentiment

    articles = NewsArticle.objects.filter(sentiment__isnull=True) | NewsArticle.objects.filter(sentiment="")
    # 建立對應字典
    sentiment_mapping = {
        "-1": "negative",
        "0": "neutral",
        "1": "positive"
    }

    for article in articles:
        if article.content:  # 確保 content 欄位有內容
            sentiment_value = predict_sentiment(article.content)  # 取得 -1, 0, 1
            article.sentiment = sentiment_mapping.get(sentiment_value, "neutral")  # 預設為 neutral
            article.save()
            print(article)

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


def test():
    news_crawler()
