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
    def insert_sql(website_name, articles):
        try:
            # 檢查網站是否存在
            website, created = NewsWebsite.objects.get_or_create(name=website_name)

            # 插入文章資料
            for article in articles:
                # 檢查文章是否已存在
                if not NewsArticle.objects.filter(title=article[0]).exists():
                    # 如果該標題不存在，創建新文章
                    NewsArticle.objects.create(
                        title=article[0],
                        url=article[1],
                        time=article[2],
                        website=website,
                        image_url=article[3]
                    )

            print(f"{website_name} 資料成功插入！")

        except Exception as e:
            print(f"{website_name} 出現錯誤")
            print(f"錯誤訊息: {e}")
    
    def no_content():
        try:
            # 查詢 content 為 NULL 的文章
            articles = NewsArticle.objects.filter(content__isnull=True)

            # 將結果存入列表
            data = []
            for article in articles:
                data.append([article.id, article.website.id, article.url])
            
            if not data:
                print("No articles found with no content.")
            
            return data
        
        except Exception as e:
            print("no_content() 出現錯誤")
            print(f"錯誤訊息: {e}")
            return []

    def insert_content(id, data):
        try:
            # 查詢 article 是否存在
            article = NewsArticle.objects.get(id=id)

            if article.image_url:
                # 只更新 content
                article.content = data[0]
            else:
                # 更新 content 和 image_url
                article.content = data[0]
                article.image_url = data[1]

            # 保存更改
            article.save()
            
        except NewsArticle.DoesNotExist:
            print(f"文章 {id} 不存在")
        except Exception as e:
            print(f"{id} 出現錯誤")
            print(f"錯誤訊息: {e}")

    def insert_image_url(name, icon_url):
        try:
            # 使用 get_or_create 來插入或更新資料
            website, created = NewsWebsite.objects.update_or_create(
                name=name,  # 查找條件：根據網站名稱
                defaults={'icon_url': icon_url}  # 更新 icon_url
            )

            if created:
                print(f"{name} 資料成功插入！")
            else:
                print(f"{name} 資料已更新！")

        except Exception as e:
            print(f"{name} 出現錯誤")
            print(f"錯誤訊息: {e}")
    
    insert_sql(*fetch_investing())
    insert_sql(*fetch_coindesk())
    insert_sql(*fetch_yahoo())
    for i in no_content():
        insert_content(i[0],fetch_content(i[1],i[2]))
        print(i[0],i[2] ,"資料插入成功")

        insert_image_url("https://hk.investing.com/news/cryptocurrency-news", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcrwkwizaO4rpZ8b4af74qxlZKh6YK98JjGw&s")
        insert_image_url("https://www.coindesk.com/", "https://logos-world.net/wp-content/uploads/2023/02/CoinDesk-Logo.png")
        insert_image_url("https://finance.yahoo.com/topic/crypto/", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Yahoo%21_Finance_logo_2021.png/1200px-Yahoo%21_Finance_logo_2021.png")
    return "任務完成"