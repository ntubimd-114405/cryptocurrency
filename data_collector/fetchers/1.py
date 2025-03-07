import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# 設定要搜尋的關鍵字和時間範圍
keyword = 'BTC'
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)

# 爬取 Reddit 上的帖子
url = f'https://www.reddit.com/r/cryptocurrency/search?q={keyword}&restrict_sr=1&t=hour'
headers = {'User-Agent': 'Mozilla/5.0'}

response = requests.get(url, headers=headers)

# 檢查請求是否成功
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    # 計算符合條件的帖子數量
    tweet_count = 0
    posts = soup.find_all('div', class_='Post')

    for post in posts:
        # 獲取帖子的時間
        timestamp = post.find('time')
        if timestamp:
            post_time = datetime.fromtimestamp(int(timestamp['data-time']) if 'data-time' in timestamp.attrs else 0)
            if start_time <= post_time <= end_time:
                tweet_count += 1
                title_element = post.find('a', {'data-testid': 'post-title'})
                if title_element:
                    title = title_element.text
                    print(f'[{post_time}] {title}')

    print(f'過去1小時內有 {tweet_count} 條關於 "{keyword}" 的帖子')
else:
    print('無法訪問 Reddit 網站，請檢查 URL 或網絡連接。')
