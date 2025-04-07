from celery import shared_task
from datetime import datetime, timedelta
from dateutil import parser
from data_collector.coin_history.ccxt_price import CryptoHistoryFetcher

@shared_task
def news_crawler():
    from .models import Website,Article
    from django.db.models import Q
    from data_collector.new_scraper import site_all

    websites=site_all.website()
    for site in websites:
        Website.objects.update_or_create(
                url=site.url,
                defaults={
                "name":site.name,
                'icon_url': site.icon_url,
            },
            )
        website_instance = Website.objects.get(name=site.name)
        
        for article in site.fetch_page():
            defaults = {
            'website': website_instance
            }

            # 如果 image_url 存在，加入到 defaults
            if article.get("image_url"):
                defaults['image_url'] = article["image_url"]

            Article.objects.update_or_create(
                url=article["url"],
                defaults=defaults,
            )
    articles_empty = Article.objects.filter(
        Q(content__isnull=True) | Q(content__exact="") |
        Q(title__isnull=True) | Q(title__exact="") |  
        Q(time__isnull=True) | Q(image_url__isnull=True)
    ).order_by('-id')[:10]
    #articles_empty = NewsArticle.objects.all()
    print(len(articles_empty))
    for article in articles_empty:
        try:
            a=site_all.article(article)
            if a:
                a.get_news_details()
                Article.objects.update_or_create(
                        url=a.url,
                        defaults={
                        'title': a.title,
                        'time': a.time,
                        'image_url':a.image_url,
                        "content":a.content,
                        'summary':a.summary,
                        'website':a.website
                    },
                    )
                print(article.id,a.title)
        except Exception as e:
            print(f"發生錯誤: {e}")
            continue

@shared_task
def news_sentiment():
    from .models import Article
    from data_analysis.sentiment.multi_model_voting import predict_sentiment

    articles = Article.objects.filter(sentiment__isnull=True) | Article.objects.filter(sentiment="")
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

def test():
    news_crawler()


