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





@shared_task
def fetch_history():
    from django.db.models import Max
    from .models import Coin,CoinHistory
    from celery import group

    coin_history = Coin.objects.all().order_by('id')[:3]
    result = []
    for coin in coin_history:
        # 查找該 coin 的最新日期
        latest_history = CoinHistory.objects.filter(coin=coin).aggregate(latest_date=Max('date'))
        latest_date = latest_history['latest_date']

        # 若找不到最新日期，設定為 2025-01-01
        if latest_date is None:
            latest_date = datetime(2023, 1, 1, 0, 0)
        else:
            latest_date = latest_date + timedelta(minutes=1)
        result.append((coin, latest_date))
    
    for i in result:
        c=CryptoHistoryFetcher(i[0].abbreviation,i[1])
        coin = Coin.objects.get(abbreviation=c.coin,api_id=i[0].api_id)
        data=c.get_history()
        for history_data in data:
            date = datetime.strptime(history_data[0], '%Y-%m-%d %H:%M:%S')
            date=str(date)+"+00:00"
            open_price = history_data[1]
            high_price = history_data[2]
            low_price = history_data[3]
            close_price = history_data[4]
            volume = history_data[5]
            
            # 儲存歷史資料進入資料庫
            CoinHistory.objects.create(
                coin=coin,
                date=date,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
            )
        if data:  # 確保 history_data 不為空
            print(f"存入資料庫{len(data)}筆：{c.coin} {history_data[0]}")
        else:
            print(f"沒有資料存入資料庫{len(data)}筆：{c.coin} {c.starttime}")