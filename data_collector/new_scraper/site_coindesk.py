from .base_site import BaseArticle,BaseWebsite,convert_emoji_to_text
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import re
import time
from urllib.parse import urlparse, parse_qs

def parse_relative_time(relative_time):
    try:
        now = datetime.now()
        time_mapping = {
            "hour ago": "hours",
            "hours ago": "hours",
            "HRS AGO": "hours",
            "HR AGO": "hours",
            "minute ago": "minutes",
            "minutes ago": "minutes",
            "MINS AGO": "minutes",
            "MIN AGO": "minutes",
            "DAYS AGO": "days",
            "DAY AGO": "days",
        }
        # 分割字串
        if ',' in relative_time:
            # 解析 "Jul 10, 2024" 類型的日期
            return datetime.strptime(relative_time, "%b %d, %Y")

        # 處理相對時間（例如：3 hours ago, 5 days ago）
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
    

def parse_relative_time2(text):
    pattern = r"([A-Za-z]+\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s*[ap]\.m\.\s+UTC)"
    match = re.search(pattern, text)
    if match:
        time_str = match.group(1)
        # 將 'a.m.' 與 'p.m.' 轉換成 datetime 模組可解析的格式
        time_str = time_str.replace("a.m.", "AM").replace("p.m.", "PM")
        # 移除 " UTC" 部分，稍後再指定時區
        time_str = time_str.replace(" UTC", "")
        # 移除前後多餘的空白字元
        time_str = time_str.strip()
        
        # 使用 strptime 解析字串，格式為：%b 表示英文月份縮寫，%d 日，%Y 年，%I 小時（12小時制），%M 分，%p AM/PM
        dt = datetime.strptime(time_str, "%b %d, %Y, %I:%M %p")
        # 設定時區為 UTC
        dt = dt.replace(tzinfo=timezone.utc)
        return dt
    else:
        return None


class CoindeskWebsite(BaseWebsite):
    def __init__(self):
        self.name = "coindesk"
        self.url = "https://www.coindesk.com/"
        self.icon_url = "https://logos-world.net/wp-content/uploads/2023/02/CoinDesk-Logo.png"
    

    def fetch_page(self):
        data=[]
        response = requests.get("https://www.coindesk.com/latest-crypto-news")
        soup = BeautifulSoup(response.text, 'html.parser')

        # 找到文章列表
        articles = soup.find_all(class_='flex flex-col')
        for article in articles:
            title = article.find('h2')  # 假設每篇文章的標題都在 <h2> 標籤中
            if title:
                title = convert_emoji_to_text(title.text)
            else:
                title = None
            link = article.find('a', class_="text-color-charcoal-900 mb-4 hover:underline")
            if link is None:
                continue  
            link=link["href"]
            link = link.split("https://www.coindesk.com")[-1]
            
            time = article.find('span', class_="Noto_Sans_xs_Sans-400-xs")
            if time is None:continue
            time=time.text
            time=parse_relative_time(time)
            if time is None:continue
            time=str(time)+"+08:00"

            data.append({"title":title, "url":f"https://www.coindesk.com{link}", "time":time})
        return data

class CoindeskArticle(BaseArticle):
    def __init__(self, data):
        self.url = data.url
        self.title = data.title
        self.content = data.content
        self.image_url = data.image_url
        self.time = data.time
        self.website = data.website
        self.summary = data.summary

    def is_complete(self):
        return all([self.url, self.title, self.content, self.time, self.website])
    

    def get_news_details(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')


        # 找到 img 標籤
        title_tag = soup.find('h1',class_="text-headline-lg")
        if title_tag is None:
            title = (self.url.split("/")[-1]).replace("-"," ")
        else:
            title = title_tag.text.strip()
        self.title = title.encode('ascii', 'ignore').decode('ascii')

        summary_tag = soup.find('h2',class_="text-body-large")
        if summary_tag is None:
            summary=None
        else:
            summary = summary_tag.text.strip()
            self.summary = summary

        content_divs = [div.get_text(strip=True) for div in soup.find_all('div', class_='document-body') if div.get_text(strip=True)]
        if content_divs:
            content = ' '.join(content_divs)
            if content:
                self.content=convert_emoji_to_text(content).encode('ascii', 'ignore').decode('ascii')


        img_tag = soup.find('img',class_="rounded-md")
        if img_tag is None:
            og_image = soup.find("meta", property="og:image")
            url = og_image["content"] if og_image else None  # 若找不到 <img>，則用 og:image
        else:
            url = img_tag.get('url')
            if url is None:
                url=img_tag.get('src')
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                url = query_params.get("url", [None])[0]

        self.image_url = url

        time_tag = soup.find('span',class_="md:ml-2")
        if time_tag:
            t = time_tag.get_text()
            t = parse_relative_time2(t)
            if t:
                self.time = t
        else:
            t = None
        
        
        
        
        





