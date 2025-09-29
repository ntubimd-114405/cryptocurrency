from .base_site import BaseArticle,BaseWebsite,convert_emoji_to_text
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

class InvestingWebsite(BaseWebsite):
    def __init__(self):
        self.name = "investing"
        self.url = "https://hk.investing.com/news/cryptocurrency-news"
        self.icon_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcrwkwizaO4rpZ8b4af74qxlZKh6YK98JjGw&s"
    

    def fetch_page(self):
        try:
            options = Options()
            #options.add_argument("--headless")  # 不開啟瀏覽器視窗
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--ignore-certificate-errors")  # 忽略 SSL 錯誤
            options.add_argument("--allow-insecure-localhost")  # 允許不安全的連線
            options.add_argument("--disable-logging")  # 減少日誌輸出
            options.add_argument("--log-level=3")  # 設定 Chrome 最低日誌級別
            options.add_argument("--disable-webgl")
            options.add_argument("--disable-software-rasterizer")
            options.add_experimental_option("excludeSwitches", ["enable-logging"])  # 隱藏 DevTools 訊息
            service = Service("data_collector/new_scraper/chromedriver.exe")  # 設定 ChromeDriver 路徑
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.get(self.url)
            time.sleep(15)  # 等待 JavaScript 加載
            try:
                driver.find_element(By.XPATH,u"(.//*[normalize-space(text()) and normalize-space(.)='完全同步APP應用程式'])[1]/following::*[name()='svg'][1]").click()
            except:
                pass
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
            
            data = []
            articles = soup.find_all("article", {"data-test": "article-item"})
            for article in articles:
                title_element = article.find("a", {"data-test": "article-title-link"})
                title = title_element.get_text(strip=True) if title_element else "N/A"

                # 找連結
                link = title_element["href"] if title_element else "#"

                # 找時間
                time_element = article.find("time", {"data-test": "article-publish-date"})
                time_text = time_element["datetime"] + "+00:00" if time_element else "N/A"

                data.append({
                    "title": title,
                    "url": link,
                    "time": time_text,
                    "image_url": None
                })
            return data
        except Exception as e:       
            print(f"錯誤: {e}")
            return []



class InvestingArticle(BaseArticle):
    def __init__(self, data):
        self.url = data.url
        self.title = data.title
        self.content = data.content
        self.image_url = data.image_url
        self.time = data.time
        self.website = data.website
        self.summary = data.summary


    def get_news_details(self):
        options = Options()
        #options.add_argument("--headless")  # 不開啟瀏覽器視窗
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")  # 忽略 SSL 錯誤
        options.add_argument("--allow-insecure-localhost")  # 允許不安全的連線
        options.add_argument("--disable-logging")  # 減少日誌輸出
        options.add_argument("--log-level=3")  # 設定 Chrome 最低日誌級別
        options.add_argument("--disable-webgl")
        options.add_argument("--disable-software-rasterizer")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])  # 隱藏 DevTools 訊息
        service = Service("data_collector/new_scraper/chromedriver.exe")  # 設定 ChromeDriver 路徑
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(self.url)
        # 等待頁面加載完成
        time.sleep(3)
        try:
            driver.find_element(By.XPATH,u"(.//*[normalize-space(text()) and normalize-space(.)='完全同步APP應用程式'])[1]/following::*[name()='svg'][1]").click()
        except:
            pass
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        # 取得標題
        title_element = soup.find(id="articleTitle")

        if title_element:
            self.title = title_element.get_text(strip=True)

        # 取得內容
        content_element = soup.find('div', class_="article_WYSIWYG__O0uhw article_articlePage__UMz3q text-[18px] leading-8")
        if content_element:
            paragraphs = content_element.find_all('p')
            # 提取所有 p 標籤的文本
            if paragraphs:
                self.content = convert_emoji_to_text("\n".join([p.get_text(strip=True) for p in paragraphs]))

        # 取得發佈時間
        time_element = soup.find("div", class_="flex flex-col gap-2 text-warren-gray-700 md:flex-row md:items-center md:gap-0")
        if time_element:
            time_str = time_element.find("span")
            time_str = time_str.get_text(strip=True)

            time_str = time_str.replace("發布", "").strip()
            time_str = time_str.replace("下午", "PM").replace("上午", "AM")

            # 假設時間格式為 '2025-4-2 下午05:43'
            # 轉換成 datetime 物件，先處理中文 "下午" 和時間格式
            time_hk = datetime.strptime(time_str, "%Y-%m-%d %p%I:%M")

            # 設定香港時間是 UTC+8，將時間減去 8 小時以轉換成 UTC 時間
            time_utc = time_hk - timedelta(hours=8)
            # 格式化 UTC 時間

            self.time = time_utc.replace(tzinfo=timezone.utc)

        # 取得圖片
        img_element = soup.find("img", class_="h-full w-full object-contain")
        if img_element:
            self.image_url = img_element.get("src")





