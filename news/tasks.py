from celery import shared_task
from datetime import datetime, timedelta
from dateutil import parser
from data_collector.coin_history.ccxt_price import CryptoHistoryFetcher
from data_analysis.crypto_ai_agent.news_agent import initialize_news_vector_store

#4-1 新聞爬蟲
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
#4-2 文章插入與更新資料庫過程----       
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
#----4-2 文章插入與更新資料庫過程  
#4-3 取得新聞詳細內容
    articles_empty = Article.objects.filter(
        Q(content__isnull=True) | Q(content__exact="") |
        Q(title__isnull=True) | Q(title__exact="") |  
        Q(time__isnull=True) | Q(image_url__isnull=True) 
    ).order_by('-id')[:20]
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

# 6-1 文章情緒分析
@shared_task
def news_sentiment():
    from news.models import Article
    from data_analysis.sentiment.multi_model_voting import predict_sentiment
    """
    批次分析情緒，每次抓 10 篇未分析文章，有 summary，依時間最新排序
    """
    print(f"分析情緒")
    # 篩選條件：summary 不為空 & sentiment_score 為空或 null
    articles = Article.objects.filter(
        summary__isnull=False
    ).exclude(
        summary=""
    ).filter(
        sentiment_score__isnull=True
    ).order_by('-time')[:10]  # 切片放在最後，沒再呼叫 order_by


    for article in articles:
        print(f"Processing Article ID: {article.id}, Title: {article.title}")
        # 使用 summary 進行情緒分析
        sentiment, score = predict_sentiment(article.title + article.summary)

        # 存回模型
        article.sentiment_score = score
        article.save()
    
    return f"Processed {len(articles)} articles."



#5-1 文章摘要
@shared_task
def news_summary():
    from news.models import Article
    from data_analysis.sentiment.summary import summarize_long_text  # 你的摘要程式
    """
    批次生成摘要，每次抓 10 篇 content 不為空且 summary 為空的文章
    """
    print(f"生成摘要")
    # 篩選條件：content 不為空 & summary 為空或 null
    articles = Article.objects.filter(
        content__isnull=False
    ).exclude(
        content=""
    ).filter(
        summary__isnull=True
    ) | Article.objects.filter(
        content__isnull=False
    ).exclude(
        content=""
    ).filter(
        summary=""
    )

    # 依時間最新排序，只取前 10 筆
    articles = articles.order_by('-time')[:10]

    processed_count = 0
    for article in articles:
        print(f"Processing Article ID: {article.id}, Title: {article.title}")
        summary = summarize_long_text(article.content)
        if summary:
            article.summary = summary
            article.save()
            processed_count += 1

    return f"Processed {processed_count} articles."





@shared_task
def refresh_news_vector_store():
    initialize_news_vector_store()





