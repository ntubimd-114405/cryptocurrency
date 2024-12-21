from celery import shared_task
from datetime import datetime

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptocurrency.settings')
@shared_task
def run_scraper():
    from .models import NewsWebsite,NewsArticle
    print("任務正在執行...")
    title = "Sample News Article"
    url = "https://example.com/news-article"
    image_url = "https://example.com/sample-image.jpg"
    content = "This is the content of the sample news article."
    time = datetime.now()  # 使用當前時間
    website_name = "Example News"

    # 取得 NewsWebsite 實體（假設您已經有對應的網站資料）
    website, created = NewsWebsite.objects.get_or_create(name=website_name)

    # 將資料儲存到 NewsArticle
    NewsArticle.objects.create(
        title=title,
        url=url,
        image_url=image_url,
        content=content,
        time=time,
        website=website
    )
    return "任務完成"