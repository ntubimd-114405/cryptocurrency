from .base_site import BaseArticle,BaseWebsite,convert_emoji_to_text
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

class YahooWebsite(BaseWebsite):
    def __init__(self):
        self.name = "Yahoo"
        self.url = "https://finance.yahoo.com/topic/crypto/"
        self.icon_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Yahoo%21_Finance_logo_2021.png/1200px-Yahoo%21_Finance_logo_2021.png"
    
    def fetch_page(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }

        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        data = []
        current_time = datetime.now()
        articles = soup.find_all('div', class_="content")
        for article in articles:
            link_tag = article.find('a')
            link = link_tag['href'] if link_tag and link_tag.has_attr('href') else None
            if "https://finance.yahoo.com" not in link:continue

            # 提取標題（h2 或 h3）
            title_tag = article.find(['h3'], class_=['clamp yf-82qtw3'])
            title = title_tag.text.strip() if title_tag else None


            # 提取時間
            time_tag = article.find('div', class_='publishing')
            time_str = time_tag.text.strip() if time_tag else None
            
            img_tag = article.find('img')

            img = None
            if img_tag:
                img = img_tag['src']
            # 處理時間格式
            time = None
            if time_str != None:

                # 提取時間描述，如 "12 hours ago"
                time_match = re.search(r'(\d+)\s*(days|hour|minute|second)s?\s*ago', time_str)
                if time_match:
                    number = int(time_match.group(1))
                    unit = time_match.group(2)
                    if unit == "days":
                        time = current_time - timedelta(days=number)
                    elif unit == "hour":
                        time = current_time - timedelta(hours=number)
                    elif unit == "minute":
                        time = current_time - timedelta(minutes=number)
                    elif unit == "second":
                        time = current_time - timedelta(seconds=number)
                elif  "yesterday" in time_str:
                    time = current_time - timedelta(days=1)             


                time = time.strftime('%Y-%m-%d %H:%M:%S+08:00')


            # 保存結果
            data.append({"title":title,"url":link, "time":time,"image_url":img})

        return data


class YahooArticle(BaseArticle):
    def __init__(self, data):
        self.url = data.url
        self.title = data.title
        self.content = data.content
        self.image_url = data.image_url
        self.time = data.time
        self.website = data.website
        self.summary = ""


    def get_news_details(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content = soup.find('div', class_='atoms-wrapper')
        if content:
            content=content.get_text(strip=True)
            self.content=convert_emoji_to_text(content)

        img_tag = soup.find('img',class_="yf-g633g8")
        if img_tag:
            img_url=img_tag.get('src')
            if  not "data:image/gif;" in img_url:
                self.image_url=img_url
            


        title = soup.find('div', class_='cover-title')
        if title:
            self.title=title.get_text(strip=True)

        time_tag = soup.find("time", class_="byline-attr-meta-time")

        if time_tag:
            # 獲取 datetime 屬性
            self.time = time_tag.get("datetime")


