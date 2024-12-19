import requests
from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).resolve().parents[3] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)
# Your Bearer Token (OAuth 2.0 App-only)
bearer_token = os.getenv('X_BEARER_TOKEN')
# The URL for the search tweets endpoint
def get_x():
    data=[]
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
    'query': 'from:realdonaldtrump -Auto-reply',  # 查询条件
    'max_results': 10,  # 返回最多10条结果
    'tweet.fields': 'id,text'  # 获取推文的 id 和 text 字段
    }
    # 設定標頭，包含 Authorization
    headers = {
        'Authorization': f'Bearer {bearer_token}'
    }

    # 發送 GET 請求
    response = requests.get(url, headers=headers , params=params)

    # 檢查響應狀態碼
    if response.status_code == 200:
        # 解析 JSON 格式的回應
        data = response.json()
        
        # 提取所有推文的 id
        tweet = [[tweet['id'],tweet['text']] for tweet in data['data']]

        # 打印所有推文的 id
        return tweet
    else:
        # 打印錯誤訊息
        print(f"Error: {response.status_code}")
        print(response.text)

def get_html(id):
    url = "https://publish.twitter.com/oembed"
    tweet_url = f"https://x.com/realDonaldTrump/status/{id}"
    params = {
    'url': tweet_url,
    'hide_media': 'true',  # 可以選擇隱藏媒體內容
    'hide_thread': 'true',  # 可以選擇隱藏回覆線程
    }
    response = requests.get(url, params=params)

    # 檢查請求是否成功
    if response.status_code == 200:
        # 獲取嵌入代碼
        embed_code = response.json().get('html')
        return embed_code
    else:
        print(f"Error: {response.status_code}")
        print(response.text)