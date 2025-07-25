import os
import json
import re
from collections import Counter
from decimal import Decimal
from datetime import date,datetime,timedelta

import numpy as np
import pandas as pd
import ta
from django.utils import timezone
from django.conf import settings
from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.db import IntegrityError
from django.urls import reverse

from .models import WeeklyReport
from main.models import CoinHistory,Coin
from news.models import Article
from other.models import FinancialData, IndicatorValue, BitcoinMetricData

from data_analysis.text_generation.chatgpt_api import call_chatgpt
from data_analysis.crypto_ai_agent.news_agent import run_news_agent


def load_price_data_from_db(coin_id, start_date=None, end_date=None):
    queryset = CoinHistory.objects.filter(coin_id=coin_id)
    name = Coin.objects.get(id=1).coinname
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

    daily_df = df.resample('1D').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna().reset_index()

    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        daily_df[col] = daily_df[col].astype(float)

    return name,daily_df

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

    recent_time = timezone.now() - timedelta(days=7)
    articles = Article.objects.filter(time__gte=recent_time).order_by('-time')[:100]
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
def full_month_data_view():
    today = timezone.now().date()
    start_date = today - timedelta(days=120)

    # 📈 FinancialData 資料
    financial_qs = FinancialData.objects.select_related('symbol').filter(date__range=(start_date, today))
    financial_df = pd.DataFrame(list(financial_qs.values(
        'symbol__symbol', 'symbol__name', 'date',
        'open_price', 'high_price', 'low_price', 'close_price', 'volume'
    )))

    # 🧠 IndicatorValue 資料
    indicator_qs = IndicatorValue.objects.select_related('indicator').filter(date__range=(start_date, today))
    indicator_df = pd.DataFrame(list(indicator_qs.values(
        'indicator__name', 'indicator__abbreviation', 'date', 'value'
    )))

    # 🔗 BitcoinMetricData 資料
    bitcoin_qs = BitcoinMetricData.objects.select_related('metric').filter(date__range=(start_date, today))
    bitcoin_df = pd.DataFrame(list(bitcoin_qs.values(
        'metric__name', 'metric__unit', 'metric__period', 'date', 'value'
    )))

    # 📊 轉為 JSON 傳到模板（或可以之後轉為 REST API）
    return {
        'financial_data_json': financial_df.to_json(orient='records', date_format='iso'),
        'indicator_data_json': indicator_df.to_json(orient='records', date_format='iso'),
        'bitcoin_data_json': bitcoin_df.to_json(orient='records', date_format='iso'),
    }



@login_required
def report_list(request):
    user = request.user
    reports = WeeklyReport.objects.filter(user=user).order_by('-year', '-week')

    today = now().date()
    this_year, this_week, _ = today.isocalendar()

    # 年份範圍：2022到今年
    year_list = list(range(2022, this_year + 1))

    # 建立一個 dict，key: 年，value: 該年可選週數列表
    weeks_by_year = {}
    for year in year_list:
        if year == this_year:
            weeks_by_year[year] = list(range(1, this_week + 1))  # 今年限定到本週
        else:
            weeks_by_year[year] = list(range(1, 54))  # 其他年份全週

    context = {
        'reports': reports,
        'year_list': year_list,
        'weeks_by_year': weeks_by_year,
        'this_year': this_year,
        'this_week': this_week,
    }

    return render(request, 'weekly_report_list.html', context)



def convert_id_and_newline(text: str) -> str:
    pattern = r"\(id:(\d+)\)"

    def replace_func(match):
        article_id = match.group(1)
        url = reverse('news_detail', kwargs={'article_id': article_id})
        return f'<a href="{url}">(id:{article_id})</a>'

    # 換連結
    replaced_text = re.sub(pattern, replace_func, text)
    # 換行轉成 <br>
    replaced_text = replaced_text.replace('\n', '<br>')

    return replaced_text


@login_required
def generate_weekly_report(request):
    user = request.user
    today = now().date()
    year = int(request.POST.get("year", today.isocalendar()[0]))
    week = int(request.POST.get("week", today.isocalendar()[1]))
    print(year,week)
    # ✅ 根據 year 和 week 計算出 start_date（週一）與 end_date（週日）
    start_date = date.fromisocalendar(year, week, 1)
    end_date = start_date + timedelta(days=6)

    # 重新計算資料
    coin,df = load_price_data_from_db(1)  # 或 user.id，視你的邏輯
    df = add_technical_indicators(df).tail(30)

    ma20_data = decimal_to_float(df['ma20'].tolist())
    ma60_data = decimal_to_float(df['ma60'].tolist())

    

    recent_articles = get_recent_articles()
    news_text = " ".join([i.title for i in recent_articles])
    word_freqs = process_word_frequencies(news_text)

    news_summary = run_news_agent("BTC") #目前寫死
    news_summary_with_links = convert_id_and_newline(news_summary)
    
    data = {
        "MA20": list(ma20_data[-7:]),
        "MA60": list(ma60_data[-7:]),
        "RSI": df['rsi_point'].dropna().tail(7).tolist(),
        "MACD": df['macd_bar'].dropna().tail(7).tolist(),
        "MACD_Signal": df['macd_signal_line'].dropna().tail(7).tolist(),
        "OHLC": df['ohlc'].dropna().tail(7).tolist(),
    }
    formatted = json.dumps(data, ensure_ascii=False)

    coin_analysis = call_chatgpt(
        system="你是一位專業金融分析師，請用 HTML <div> 包裝你的技術分析評論。",
        text=f"""請依據以下加密貨幣 {coin} 的技術分析資料進行簡潔評論，描述目前市場趨勢與可能的變化，避免逐筆說明，只需總體分析與解釋。請輸出為一段 HTML <div>...</div>，不要額外文字：
        {formatted}
        """
    ).strip("```").strip("html")

    summary = call_chatgpt(
        system="你是一位擅長撰寫財經總結的分析師。",
        text=f"""
        請你以專業金融分析師口吻，綜合以下兩部分內容，撰寫一段中文市場總結。  
        請先用段落簡短介紹市場狀況，  
        接著用 HTML 的 <table> 元素，建立一個兩欄的表格，  
        左欄標題為「利多因素」，右欄標題為「利空因素」，  
        整段內容用 <div> 包起來，且不要額外文字。

        1. 技術分析評論：
        {coin_analysis}

        2. 近期新聞摘要：
        {news_summary}
        """
    ).strip("```").strip("html").strip()

    # 📊 中長期觀點資料整合
    monthly_data = full_month_data_view()
    financial_json = monthly_data['financial_data_json']
    indicator_json = monthly_data['indicator_data_json']
    bitcoin_json = monthly_data['bitcoin_data_json']

    long_term_analysis = call_chatgpt(
        system="你是一位金融市場研究員，請撰寫中長期觀察與趨勢預測。",
        text=f"""
        請你以金融分析師身份，根據以下三類資料，撰寫一段純文字格式的中長期市場觀察與趨勢預測分析。
        請避免逐筆列舉資料，僅需從總體層面做出解釋與預測，語氣請保持客觀、專業，避免使用過多不確定詞。
        請直接輸出文字，不要使用 HTML 格式與額外標記。
        資料如下：
        1. 金融價格資料（financial_data_json）：
        {financial_json[:100]}

        2. 技術指標資料（indicator_data_json）：
        {indicator_json[:100]}

        3. 比特幣鏈上指標資料（bitcoin_data_json）：
        {bitcoin_json[:100]}
        """
    ).strip("```").strip("html").strip()

    # 更新或新增本週報告
    WeeklyReport.objects.update_or_create(
        user=user,
        year=year,
        week=week,
        defaults={
            'start_date': start_date,
            'end_date': end_date,
            'summary': summary,
            'news_summary': news_summary_with_links,
            'word_frequencies': word_freqs,
            'ma20_data': ma20_data,
            'ma60_data': ma60_data,
            'ohlc_data': df['ohlc'].tolist(),
            'rsi_data': df['rsi_point'].dropna().tolist(),
            'macd_data': df['macd_bar'].dropna().tolist(),
            'macd_signal_data': df['macd_signal_line'].dropna().tolist(),
            'coin_analysis':coin_analysis,
            'financial_data_json': financial_json,
            'indicator_data_json': indicator_json,
            'bitcoin_data_json': bitcoin_json,
            'long_term_analysis': long_term_analysis,
        }
    )

    return redirect('weekly_report_list')  # 重新導向你的週報頁


@login_required
def view_weekly_report_by_id(request, report_id):
    report = get_object_or_404(WeeklyReport, id=report_id, user=request.user)

    context = {
        'summary': report.summary,
        'news_summary': report.news_summary,
        'word_freqs_json': json.dumps(report.word_frequencies),
        'ma20_data': json.dumps(report.ma20_data),
        'ma60_data': json.dumps(report.ma60_data),
        'ohlc_json': json.dumps(report.ohlc_data),
        'rsi_json': json.dumps(report.rsi_data),
        'macd_json': json.dumps(report.macd_data),
        'macd_signal_json': json.dumps(report.macd_signal_data),
        'coin_analysis':report.coin_analysis,
        'financial_data_json': report.financial_data_json,
        'indicator_data_json': report.indicator_data_json,
        'bitcoin_data_json': report.bitcoin_data_json,
        'long_term_analysis': report.long_term_analysis,
        'user': report.user,
        'year': report.year,
        'week': report.week,
        'start_date': report.start_date,
        'end_date': report.end_date,
        'created_at': report.created_at,
    }

    # 也可以把共用的 full_month_data 加進 context，如果需要
    context.update(full_month_data_view())

    return render(request, 'weekly_report.html', context)





