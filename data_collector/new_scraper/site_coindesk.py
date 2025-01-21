from .base_site import BaseArticle,BaseWebsite
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time

def parse_relative_time(relative_time):
    try:
        now = datetime.now()
        time_mapping = {
            "HRS AGO": "hours",
            "HR AGO": "hours",
            "MINS AGO": "minutes",
            "MIN AGO": "minutes",
            "DAYS AGO": "days",
            "DAY AGO": "days",
        }

        # 分割字串
        parts = relative_time.split()
        if len(parts) != 3 or f"{parts[1]} {parts[2]}" not in time_mapping:
            raise ValueError(f"Invalid format: {relative_time}")

        # 解析數字和單位
        number = int(parts[0])
        unit = time_mapping[f"{parts[1]} {parts[2]}"]

        # 根據單位計算時間
        if unit == "hours":
            return now - timedelta(hours=number)
        elif unit == "minutes":
            return now - timedelta(minutes=number)
        elif unit == "days":
            return now - timedelta(days=number)
        else:
            raise ValueError(f"Unsupported time unit: {unit}")
    except:
        return None
    
class CoindeskWebsite(BaseWebsite):
    def __init__(self):
        self.name = "coindesk"
        self.url = "https://www.coindesk.com/"
        self.icon_url = "https://logos-world.net/wp-content/uploads/2023/02/CoinDesk-Logo.png"
    

    def fetch_page(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        data=[]

        # 找到文章列表
        articles = soup.find_all(class_='bg-white flex gap-6 w-full shrink')

        for article in articles:
            title = article.find('h3').text  # 假設每篇文章的標題都在 <h2> 標籤中
            link = article.find('a', class_="text-color-charcoal-900 mb-4 hover:underline")["href"]

            time = article.find('span', class_="Noto_Sans_xs_Sans-400-xs")
            if time is None:continue
            time=time.text
            
            time=parse_relative_time(time)
            if time is None:continue
            
            time=str(time)+"+00:00"

            data.append({"title":title, "url":f"https://www.coindesk.com/{link}", "time":time})
        return data

class CoindeskArticle(BaseArticle):
    def __init__(self, data):
        self.url = data.url
        self.title = data.title
        self.content = data.content
        self.image_url = data.image_url
        self.time = data.time
        self.website = data.website

    def is_complete(self):
        return all([self.url, self.title, self.content, self.time, self.website])
    

    def get_news_details(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 找到 img 標籤
        img_tag = soup.find('img',class_="rounded-md")
        try:
            # 嘗試獲取第二個符合條件的元素
            content = soup.find_all('div', class_='document-body')[1]
        except :
            content = soup.find_all('div', class_='document-body')[0]

        # 如果成功找到內容，則提取純文本
        if content:
            content = content.get_text(strip=True)

        # 獲取自定義的 url 屬性
        if img_tag is None:
            url=None
        else:
            url = img_tag.get('url')


        self.content=content
        self.image_url = url



    def scrape(self):
        """Scrape the content of the article."""
        pass


