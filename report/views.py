# views.py

import pandas as pd
import matplotlib.pyplot as plt
import ta
import os
from wordcloud import WordCloud
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

from main.models import CoinHistory
import pandas as pd

def load_price_data_from_db(coin_id, start_date=None, end_date=None):
    queryset = CoinHistory.objects.filter(coin_id=coin_id)

    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    queryset = queryset.order_by('date').values(
        'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
    )

    df = pd.DataFrame.from_records(queryset)
    df.rename(columns={
        'date': 'Date',
        'open_price': 'Open',
        'high_price': 'High',
        'low_price': 'Low',
        'close_price': 'Close',
        'volume': 'Volume',
    }, inplace=True)

    return df

import numpy as np
def fake_load_price_data_from_db():
    # 建立日期範圍
    date_range = pd.date_range(end='2025-06-23', periods=90)

    # 建立假資料
    np.random.seed(42)
    close_prices = np.random.uniform(25000, 27000, size=len(date_range)).round(2)
    open_prices = (close_prices + np.random.uniform(-300, 300, size=len(date_range))).round(2)
    high_prices = np.maximum(close_prices, open_prices) + np.random.uniform(0, 200, size=len(date_range)).round(2)
    low_prices = np.minimum(close_prices, open_prices) - np.random.uniform(0, 200, size=len(date_range)).round(2)
    volumes = np.random.uniform(1000, 5000, size=len(date_range)).round()

    # 建立 DataFrame
    df = pd.DataFrame({
        'Date': date_range,
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volumes
    })


    return df

def add_technical_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['ma20'] = df['Close'].rolling(window=20).mean()
    df['ma50'] = df['Close'].rolling(window=50).mean()
    return df

def generate_wordcloud(text, save_path):
    folder = os.path.dirname(save_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
    wc = WordCloud(
        background_color='white',
        max_words=100,
        width=800,
        height=400
    ).generate(text)
    plt.figure(figsize=(10,5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(save_path)
    plt.close()

from django.shortcuts import render
from django.conf import settings
import os
import json
from collections import Counter
from decimal import Decimal

from collections import Counter
import re
import json

def process_word_frequencies(news_text):
    # 停用詞列表
    stop_words = {
        'from', 'with', 'as', 'in', 'the', 'to', 'and', 'on', 'for', 'of', 'by', 
        'at', 'is', 'are', 'has', 'have', 'over', 'about', 'amid'
    }
    
    # 清理文本：移除標點並轉為小寫
    words = re.sub(r'[^\w\s]', '', news_text.lower()).split()
    # 過濾停用詞
    words = [word for word in words if word not in stop_words]
    
    # 計算詞頻
    counter = Counter(words)
    
    # 關鍵詞加權
    key_words = {
        'bitcoin': 1.5,
        'etf': 1.5,
        'crypto': 1.3,
        'ethereum': 1.3,
        'solana': 1.2,
        'defi': 1.2,
        'market': 1.1,
        'inflation': 1.1
    }
    
    # 生成詞頻列表並應用加權
    word_freqs = [(word, count * key_words.get(word, 1.0)) for word, count in counter.items()]
    
    # 按頻次降序排序並限制詞彙數量（避免過多）
    word_freqs = sorted(word_freqs, key=lambda x: x[1], reverse=True)[:30]
    
    return word_freqs

def decimal_to_float(data_list):
    return [float(val) if isinstance(val, Decimal) else val for val in data_list]

def weekly_report_view(request):
    report_dir = os.path.join(settings.MEDIA_ROOT, 'report')
    os.makedirs(report_dir, exist_ok=True)

    wordcloud_img_filename = 'news_wordcloud.png'
    wordcloud_img_path = os.path.join(report_dir, wordcloud_img_filename)

    # 取得資料與技術指標
    df = load_price_data_from_db(coin_id=1, start_date='2025-05-20', end_date='2025-06-23')
    df = fake_load_price_data_from_db() #假資料
    
    df = add_technical_indicators(df).tail(30)  # 最近 30 天

    # 將圖表資料轉為 list 傳到前端
    price_labels = df['Date'].dt.strftime('%Y-%m-%d').tolist()
    close_data = df['Close'].tolist()
    ma20_data = df['ma20'].tolist()
    ma50_data = df['ma50'].tolist()



    # 假設這是你預處理好的文字（未分詞）
    news_text = """
    Bitcoin ETF approval sparks optimism in the crypto market, boosting investor confidence. 
    Inflation concerns ease as macroeconomic indicators stabilize. 
    FUD from regulators persists, with discussions on stricter crypto oversight. 
    Ethereum shows resilience despite market volatility, driven by DeFi growth. 
    Solana gains traction with faster transaction speeds and lower fees. 
    Institutional adoption of cryptocurrencies accelerates, with major firms allocating funds to BTC and ETH. 
    Market sentiment remains cautiously optimistic, with analysts predicting a bullish trend for Q4. 
    Stablecoins face scrutiny over transparency, raising questions about reserve backing. 
    Decentralized finance continues to innovate, attracting new users globally. 
    Crypto exchanges report record trading volumes amid heightened market activity.
    """

    # 自動生成詞頻（可改成斷詞處理）
    word_freqs = process_word_frequencies(news_text)
    
    # 更新摘要
    summary = """
    本週BTC價格穩定上升，市場對ETF審批反應積極，整體情緒偏正面。
    Ethereum和Solana表現強勁，DeFi和機構採用推動市場增長。
    監管不確定性仍存，穩定幣透明度問題引發關注。
    """
    return render(request, 'weekly_report.html', {
        'summary': summary,
        'word_freqs_json': json.dumps(word_freqs),
        'price_labels': json.dumps(price_labels),
        'close_data': json.dumps(decimal_to_float(close_data)),
        'ma20_data': json.dumps(decimal_to_float(ma20_data)),
        'ma50_data': json.dumps(decimal_to_float(ma50_data)),
    })
