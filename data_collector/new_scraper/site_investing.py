from .base_site import BaseArticle,BaseWebsite,convert_emoji_to_text
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
        headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Content-Type": "text/html; charset=utf-8",
    "DNT": "1",  # Do Not Track request
    "Cookie": "udid=d493f81db9fce5947411f0ce1b9968c4; _fbp=fb.1.1732502866741.823854017412798344; _ga_FVWZ0RM4DH=GS1.1.1733228501.3.1.1733229857.60.0.0; _ga=GA1.1.643577121.1732502879",  # Cookie值
}


        response = requests.get(self.url, headers=headers)
        #print(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup)
        data=[]
        articles = soup.find_all('article', class_="article-item")
        for article in articles:
            title = article.find('a').get_text(strip=True)
            link = article.find('a')['href']  # 相對路徑
            time = article.find('time')['datetime']+"+00:00"
            data.append({"title":convert_emoji_to_text(title),"url":link, "time":time,"image_url":None})
            
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
        try:
            content = content_div.get_text(strip=True)
        except:
            content= None
        
        self.content=convert_emoji_to_text(content)
        self.image_url = img




