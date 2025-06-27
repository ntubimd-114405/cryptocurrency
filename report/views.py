import os
import json
import re
from collections import Counter
from decimal import Decimal
from datetime import datetime,timedelta

import numpy as np
import pandas as pd
import ta
from django.utils import timezone
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

from main.models import CoinHistory
from news.models import Article
# 資料庫取得資料

def load_price_data_from_db(coin_id, start_date=None, end_date=None):
    queryset = CoinHistory.objects.filter(coin_id=coin_id)

    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    queryset = queryset.order_by('-date').values(
        'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
    )[:60*24*120] #120天

    df = pd.DataFrame.from_records(queryset)
    df.rename(columns={
        'date': 'Date',
        'open_price': 'Open',
        'high_price': 'High',
        'low_price': 'Low',
        'close_price': 'Close',
        'volume': 'Volume',
    }, inplace=True)

    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    print(df)
    daily_df = df.resample('1D').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna().reset_index()

    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        daily_df[col] = daily_df[col].astype(float)

    return daily_df

# 假資料生成器（方便測試）
def fake_load_price_data_from_db():
    date_range = pd.date_range(end='2025-06-23', periods=90)
    np.random.seed(42)
    close_prices = np.random.uniform(25000, 27000, size=len(date_range)).round(2)
    open_prices = (close_prices + np.random.uniform(-300, 300, size=len(date_range))).round(2)
    high_prices = np.maximum(close_prices, open_prices) + np.random.uniform(0, 200, size=len(date_range)).round(2)
    low_prices = np.minimum(close_prices, open_prices) - np.random.uniform(0, 200, size=len(date_range)).round(2)
    volumes = np.random.uniform(1000, 5000, size=len(date_range)).round()

    df = pd.DataFrame({
        'Date': date_range,
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volumes
    })
    return df

# 技術指標計算
def add_technical_indicators(df):
    # 計算技術指標
    df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['ma20'] = df['Close'].rolling(window=20).mean()
    df['ma60'] = df['Close'].rolling(window=60).mean()

    # 將日期轉為字串格式供前端使用
    df['Date_str'] = df['Date'].dt.strftime('%Y-%m-%d')

    # 建立畫 K 線圖用欄位格式（若你使用 plotly 或 Highcharts 等）
    df['ohlc'] = df.apply(lambda row: {
        'x': row['Date_str'],
        'open': row['Open'],
        'high': row['High'],
        'low': row['Low'],
        'close': row['Close']
    }, axis=1)

    # RSI for 折線圖
    df['rsi_point'] = df.apply(lambda row: {
        'x': row['Date_str'],
        'y': row['rsi']
    }, axis=1)

    # MACD + Signal Line
    df['macd_bar'] = df.apply(lambda row: {
        'x': row['Date_str'],
        'y': row['macd']
    }, axis=1)
    df['macd_signal_line'] = df.apply(lambda row: {
        'x': row['Date_str'],
        'y': row['macd_signal']
    }, axis=1)

    return df

def get_recent_articles():

    recent_time = timezone.now() - timedelta(days=30)
    articles = Article.objects.filter(time__gte=recent_time).order_by('-time')[:10]
    return articles

# 詞頻處理（英文）
def process_word_frequencies(news_text):
    stop_words = {
        'from', 'with', 'as', 'in', 'the', 'to', 'and', 'on', 'for', 'of', 'by', 
        'at', 'is', 'are', 'has', 'have', 'over', 'about', 'amid'
    }
    words = re.sub(r'[^\w\s]', '', news_text.lower()).split()
    words = [word for word in words if word not in stop_words]
    counter = Counter(words)

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
    word_freqs = [(word, count * key_words.get(word, 1.0)) for word, count in counter.items()]
    word_freqs = sorted(word_freqs, key=lambda x: x[1], reverse=True)[:30]
    return word_freqs

# Decimal 轉 float

def decimal_to_float(data_list):
    return [float(val) if isinstance(val, Decimal) else val for val in data_list]

# 主視圖：weekly report

def weekly_report_view(request):
    report_dir = os.path.join(settings.MEDIA_ROOT, 'report')
    os.makedirs(report_dir, exist_ok=True)

    # 實際或假資料（目前使用假資料）
    df = load_price_data_from_db(1)
    #df = fake_load_price_data_from_db()
    df = add_technical_indicators(df).tail(30)
    
    ma20_data = df['ma20'].tolist()
    ma50_data = df['ma60'].tolist()

    recent_articles = get_recent_articles()
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

    word_freqs = process_word_frequencies(news_text)

    summary = """
    本週BTC價格穩定上升，市場對ETF審批反應積極，整體情緒偏正面。
    Ethereum和Solana表現強勁，DeFi和機構採用推動市場增長。
    監管不確定性仍存，穩定幣透明度問題引發關注。
    """

    return render(request, 'weekly_report.html', {
        'summary': summary,
        'word_freqs_json': json.dumps(word_freqs),
        'ma20_data': json.dumps(decimal_to_float(ma20_data)),
        'ma50_data': json.dumps(decimal_to_float(ma50_data)),
        'ohlc_json': json.dumps(df['ohlc'].tolist()),
        'rsi_json': json.dumps(df['rsi_point'].dropna().tolist()),
        'macd_json': json.dumps(df['macd_bar'].dropna().tolist()),
        'macd_signal_json': json.dumps(df['macd_signal_line'].dropna().tolist()),
        'articles': recent_articles,
    })
