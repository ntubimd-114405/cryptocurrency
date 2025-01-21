from .base_site import BaseArticle,BaseWebsite
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re


class InvestingWebsite(BaseWebsite):
    def __init__(self):
        self.name = "investing"
        self.url = "https://hk.investing.com/news/cryptocurrency-news"
        self.icon_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcrwkwizaO4rpZ8b4af74qxlZKh6YK98JjGw&s"
    

    def fetch_page(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        data=[]
        articles = soup.find_all(class_='list_list__item__dwS6E !mt-0 border-t border-solid border-[#E6E9EB] py-6')

        for article in articles:
            title = article.find('a').get_text(strip=True)
            link = article.find('a')['href']  # 相對路徑
            time = article.find('time')['datetime']+"+00:00"
            data.append({"title":title,"url":link, "time":time,"image_url":None})
        return data


class InvestingArticle(BaseArticle):
    def __init__(self, data):
        self.url = data.url
        self.title = data.title
        self.content = data.content
        self.image_url = data.image_url
        self.time = data.time
        self.website = data.website

    

    def get_news_details(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 定位內頁中的圖片標籤
        
        img = soup.find('img', class_='h-full w-full object-contain')
        if not img is None:img=img["src"]
        content_div = soup.find('div', class_='article_WYSIWYG__O0uhw article_articlePage__UMz3q text-[18px] leading-8')
        content = content_div.get_text(strip=True)
        
        self.content=content
        self.image_url = img




