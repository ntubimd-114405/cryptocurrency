from celery import shared_task
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
from .crawler.news import *

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptocurrency.settings')
@shared_task
def news_crawler():
    from .models import NewsWebsite,NewsArticle
    from data_collector.new_scraper import site_all
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
