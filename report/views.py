import os
import json
import re
from collections import Counter
from decimal import Decimal
from datetime import date,datetime,timedelta
import time

import numpy as np
import pandas as pd
import ta
from sklearn.feature_extraction.text import CountVectorizer

from django.utils import timezone
from django.conf import settings
from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.db import IntegrityError
from django.db.models import Min, Max, Sum, DateField
from django.db.models.functions import Cast
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import WeeklyReport
from main.models import CoinHistory,Coin,UserProfile, BitcoinPrice
from news.models import Article
from other.models import FinancialData, IndicatorValue, BitcoinMetricData, FinancialSymbol
from agent.models import Questionnaire, Question, AnswerOption, UserAnswer, UserQuestionnaireRecord
from data_analysis.text_generation.chatgpt_api import call_chatgpt
from data_analysis.crypto_ai_agent.news_agent import search_news

from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods




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

def get_recent_articles(start, end):
    # 假設 start 和 end 是 datetime.date 或 datetime.datetime 物件
    # 如果是日期，轉成 timezone-aware datetime 的區間
    if isinstance(start, (date,)):
        start = timezone.make_aware(datetime.combine(start, datetime.min.time()))
    if isinstance(end, (date,)):
        end = timezone.make_aware(datetime.combine(end, datetime.max.time()))

    articles = Article.objects.filter(time__gte=start, time__lte=end).order_by('-time')
    return articles


def process_word_frequency_sklearn(news_texts, top_n=30, max_features=1000):
    stop_words = [
        'the', 'in', 'to', 'and', 'of', 'on', 'for', 'with', 'at', 'by', 'a', 'an',
        'is', 'are', 'was', 'were', 'has', 'have', 'it', 'this', 'that', 'as', 'but', 'or', 'if',
        's', 'u', 'k'  # 額外噪音過濾
    ]
    if isinstance(news_texts, str):
        news_texts = [news_texts]
    vectorizer = CountVectorizer(
        stop_words=stop_words,   # 可放預設的 'english' 或自訂停用詞列表
        max_features=max_features
        )
    word_count_matrix = vectorizer.fit_transform(news_texts)
    feature_names = vectorizer.get_feature_names_out()

    # 合計所有文章的詞頻
    total_counts = word_count_matrix.sum(axis=0).A1

    # 排序，取前 top_n
    sorted_indices = total_counts.argsort()[::-1][:top_n]
    keywords = [(feature_names[i], total_counts[i]) for i in sorted_indices]
    results = [(word, int(freq)) for word, freq in keywords]
    return results



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
    # 預處理全形符號與大小寫統一
    text = text.replace('（', '(').replace('）', ')').replace('：', ':')
    
    # 定義正則，支援：
    # - (id:123)、(ID:123)
    # - id:123、ID:123
    # - 前面可有可無括號
    # - 不區分大小寫
    pattern = r"[\(]?id:(\d+)[\)]?"  # 先做簡單匹配，再做補強
    regex = re.compile(pattern, flags=re.IGNORECASE)

    def replace_func(match):
        article_id = match.group(1)
        try:
            url = reverse('news_detail', kwargs={'article_id': article_id})
            return f'<a href="{url}">(id:{article_id})</a>'
        except:
            return f"(id:{article_id})"

    # 替換成連結
    replaced_text = regex.sub(replace_func, text)
    # 換行處理
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
    
    news_summary = search_news("BTC") #目前寫死
    news_summary_with_links = convert_id_and_newline(news_summary)

    news_text = "\n".join([
        " ".join(filter(None, [
            article.title or "",
            article.summary or "",
            article.content or ""
        ]))
        for article in get_recent_articles(start_date, end_date)
    ])

    word_freqs = process_word_frequency_sklearn(news_text)
    print(call_chatgpt(
        system="你是一位專業金融分析師",
        text=f"""幫我分析以下詞頻內容
        {word_freqs}
        """
    ))
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





def my_favorite_coins_view(request):
    # 取得使用者最愛幣種及其最新價格
    favorite_coins = request.user.profile.favorite_coin.all()
    latest_prices = {}
    for coin in favorite_coins:
        price_obj = BitcoinPrice.objects.filter(coin=coin).order_by('-timestamp').first()
        if price_obj:
            latest_prices[coin.id] = price_obj

    watchlist = []
    for coin in favorite_coins:
        price = latest_prices.get(coin.id)
        if price:
            watchlist.append({
                'name': coin.coinname,
                'symbol': coin.abbreviation,
                'price': f"{price.usd:,.2f}",
                'change_24h': float(price.change_24h or 0),
                'market_cap': f"{price.market_cap:,.0f}" if price.market_cap else 'N/A',
            })
        else:
            watchlist.append({
                'name': coin.coinname,
                'symbol': coin.abbreviation,
                'price': 'N/A',
                'change_24h': 0,
                'market_cap': 'N/A',
            })
    return watchlist

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
        'watchlist': my_favorite_coins_view(request),  # <-- 加入這行
    }

    # 也可以把共用的 full_month_data 加進 context，如果需要
    context.update(full_month_data_view())

    return render(request, 'weekly_report.html', context)


def parse_coin_from_input(user_input):
    """
    用 GPT 解析使用者輸入的幣種。
    如果沒有提到，預設回傳 'BTC'。
    """
    prompt = f"""
    你是一個專業的加密貨幣助理。
    使用者會輸入一句話，可能會提到想查的幣種，例如「比特幣、BTC、bitcoin、以太坊、ETH、solana」等。
    如果有提到幣種，請回傳對應的常用代號（symbol），例如：
    - 比特幣 → BTC
    - 以太坊 → ETH
    - 狗狗幣 → DOGE
    - Solana → SOL
    - 其他就回傳最常見的交易所代號
    
    如果沒有提到任何幣種，請回傳 "BTC"。
    
    使用者輸入：{user_input}
    
    請只輸出代號，不要其他文字。
    """

    result = call_chatgpt("你是一個幣種解析助理", prompt)
    coin_symbol = result.strip().upper()
    return coin_symbol if coin_symbol else "BTC"



def run_news_agent(user_input, start_date=None, end_date=None):
    time.sleep(10)
    return {
        "text": "📰★新聞模塊",
        "extra_data": "測試資料"
    }
    """
    搜尋新聞並直接將標題轉換為可點擊連結 (news_detail)，
    並換行處理輸出 HTML
    """

    # 取得新聞資料 (list)
    news_summary = search_news(
        question=user_input,
        start_date=start_date,
        end_date=end_date
    )

    # 把 list 資料轉為 HTML
    def convert_and_link(news_list):
        text_parts = []
        for item in news_list:
            article_id = item.get("id")
            title = item.get("title", "")
            summary = item.get("summary", "")
            try:
                url = reverse('news_detail', kwargs={'article_id': article_id})
                title_html = f'<a href="{url}" target="_blank">{title}</a>'
            except:
                title_html = title
            text_parts.append(f"<b>{title_html}</b><br>{summary}")
        return "<br><br>".join(text_parts)

    news_summary_with_links = convert_and_link(news_summary)

    return {
        "text": "📰★新聞模塊",
        "extra_data": news_summary_with_links
    }




def parse_safe_date(date_str):
    """將字串轉成 date，失敗回傳 None"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None

def run_price_agent(user_input, start_date=None, end_date=None):
    coin_symbol = parse_coin_from_input(user_input)
    # 確認幣種存在
    if not Coin.objects.filter(abbreviation=coin_symbol).exists():
        return {"text": f"⚠️ 抱歉，系統內沒有找到 {coin_symbol} 的資料。", "extra_data": []}

    qs = CoinHistory.objects.filter(coin__abbreviation=coin_symbol)
    if not qs.exists():
        return {"text": f"⚠️ 模組 price 執行失敗：{coin_symbol} 暫無資料", "extra_data": []}

    # 安全轉換傳入日期
    if start_date:
        start_date = parse_safe_date(str(start_date))
    if end_date:
        end_date = parse_safe_date(str(end_date))

    # 如果沒傳日期或解析失敗 → 用資料庫最新 7 天有資料的日期
    if start_date is None or end_date is None:
        latest_days = (
            qs.annotate(day=Cast("date", output_field=DateField()))
            .values("day")
            .distinct()
            .order_by("-day")[:7]
        )
        latest_days = sorted([d["day"] for d in latest_days])
        if not latest_days:
            return {"text": f"⚠️ 模組 price 執行失敗：{coin_symbol} 暫無資料", "extra_data": []}
        start_date = latest_days[0]
        end_date = latest_days[-1]

    # 聚合查詢
    queryset = qs.annotate(day=Cast("date", output_field=DateField())) \
             .filter(day__gte=start_date, day__lte=end_date)
    daily_range = (
        queryset.annotate(day=Cast("date", output_field=DateField()))
        .values("day", "coin__coinname")
        .annotate(
            first_time=Min("date"),
            last_time=Max("date"),
            high_price=Max("high_price"),
            low_price=Min("low_price"),
            volume=Sum("volume"),
        )
        .order_by("day")
    )
    results = []
    for d in daily_range:
        first_record = qs.filter(date=d["first_time"]).first()
        last_record = qs.filter(date=d["last_time"]).first()
        results.append({
            "day": d["day"].strftime("%Y-%m-%d"),
            "coin": d["coin__coinname"],
            "open": float(first_record.open_price) if first_record else None,
            "high": float(d["high_price"]),
            "low": float(d["low_price"]),
            "close": float(last_record.close_price) if last_record else None,
            "volume": float(d["volume"]),
        })

    if not results:
        return {"text": f"⚠️ 模組 price 執行失敗：{coin_symbol} 在 {start_date} 至 {end_date} 之間沒有資料", "extra_data": []}



    return {"text": f"💰★價格模塊", "extra_data": results}





'''
def run_other_agent(user_input, start_date=None, end_date=None):
    time.sleep(3)
    return {"text": f"📊★其他經濟數據模塊,測試使用", "extra_data": "12345"}
    financial_data = FinancialData.objects.select_related("symbol").order_by("-date")
    indicator_values = IndicatorValue.objects.select_related("indicator").order_by("-date")
    btc_metrics = BitcoinMetricData.objects.select_related("metric").order_by("-date")

    if start_date:
        financial_data = financial_data.filter(date__gte=start_date)
        indicator_values = indicator_values.filter(date__gte=start_date)
        btc_metrics = btc_metrics.filter(date__gte=start_date)
    if end_date:
        financial_data = financial_data.filter(date__lte=end_date)
        indicator_values = indicator_values.filter(date__lte=end_date)
        btc_metrics = btc_metrics.filter(date__lte=end_date)

    lines = ["📊★其他經濟數據模塊"]
    lines.append("[FinancialData]")
    lines.extend([f"{x.symbol.symbol} ({x.symbol.name}): 開={x.open_price}, 高={x.high_price}, 低={x.low_price}, 收={x.close_price}, 量={x.volume}（{x.date}）" for x in financial_data[:10]])
    lines.append("[IndicatorValue]")
    lines.extend([f"{x.indicator.name}: {x.value}（{x.date}）" for x in indicator_values[:10]])
    lines.append("[BitcoinMetricData]")
    lines.extend([f"{x.metric.name}: {x.value}（{x.date}）" for x in btc_metrics[:10]])
    return "\n".join(lines)


def run_survey_agent(user_input, start_date=None, end_date=None, record_ids=None):
    queryset = UserQuestionnaireRecord.objects.select_related("user", "questionnaire").order_by("-completed_at")
    #record_ids=[1,2,5]
    # 如果指定多個 ID，直接過濾
    if record_ids:
        queryset = queryset.filter(id__in=record_ids)
    else:
        if start_date:
            queryset = queryset.filter(completed_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(completed_at__date__lte=end_date)
        queryset = queryset[:5]  # 只取最新 5 筆

    latest_records = list(queryset)

    if not latest_records:
        return {
            "text": "🧾📢★問卷模塊\n目前沒有符合條件的問卷紀錄",
            "extra_data": []
        }

    # 整理輸出文字
    records_text = "\n".join(
        f"{r.user.username} - 問卷: {r.questionnaire.title}（完成於 {r.completed_at.strftime('%Y-%m-%d %H:%M')}）"
        for r in latest_records
    )

    # 整理額外資料
    extra_data = [
        {
            "id": r.id,
            "user": r.user.username,
            "questionnaire": r.questionnaire.title,
            "completed_at": r.completed_at.isoformat()
        }
        for r in latest_records
    ]
    return {
        "text": f"🧾📢★問卷模塊\n{records_text}",
        "extra_data": extra_data
    }
    '''
def run_other_agent(user_input, start_date=None, end_date=None):

    symbol_name="GC=F"
    try:
        # 只抓指定 symbol
        symbol = FinancialSymbol.objects.get(symbol=symbol_name)
        financial_data = FinancialData.objects.filter(symbol=symbol).order_by('-date')[:10]
    except FinancialSymbol.DoesNotExist:
        return {
            "text": f"📊★金融數據模塊\n找不到 symbol: {symbol_name}",
            "extra_data": []
        }

    # 組文字輸出
    lines = [f"📊★金融數據模塊（{symbol.symbol} - {symbol.name}）"]
    for x in financial_data:
        lines.append(
            f"{x.symbol.symbol} ({x.symbol.name}): "
            f"開={x.open_price}, 高={x.high_price}, 低={x.low_price}, 收={x.close_price}, "
            f"量={x.volume}（{x.date}）"
        )

    # 回傳字典
    return {
        "text": f"📊★金融數據模塊",
        "extra_data": [
            {
                "id": x.id,
                "symbol": x.symbol.symbol,
                "name": x.symbol.name,
                "date": x.date.isoformat(),
                "open": x.open_price,
                "high": x.high_price,
                "low": x.low_price,
                "close": x.close_price,
                "volume": x.volume
            } for x in financial_data
        ]
    }


def run_survey_agent(user_input, start_date=None, end_date=None): #Fake
    # 模擬問卷資料，全部為 user123
    latest_records = [
        {
            "id": 101,
            "user": "user123",
            "questionnaire": "投資經驗",
            "completed_at": "2025-09-03T06:53:00",
            "analysis": "使用者在過去有多年的投資經驗，對加密貨幣市場波動有基本認知，偏好中低風險策略。"
        },
        {
            "id": 102,
            "user": "user123",
            "questionnaire": "基本資料",
            "completed_at": "2025-09-03T06:39:00",
            "analysis": "填寫的基本資料完整，顯示使用者對平台操作熟悉且具備財務相關背景，後續可做個人化推薦。"
        },
        {
            "id": 103,
            "user": "user123",
            "questionnaire": "合規與安全",
            "completed_at": "2025-07-07T09:51:00",
            "analysis": "使用者對合規與安全規範有一定理解，顯示其在交易時會重視風險管理與資金安全。"
        },
        {
            "id": 104,
            "user": "user123",
            "questionnaire": "交易策略與心理行為",
            "completed_at": "2025-07-07T09:51:00",
            "analysis": "填答顯示使用者偏向理性分析型，面對市場波動時較不受情緒影響，適合長期策略配置。"
        },
        {
            "id": 105,
            "user": "user123",
            "questionnaire": "未來看法與預期",
            "completed_at": "2025-07-07T09:51:00",
            "analysis": "使用者對未來市場抱持穩健樂觀態度，願意接受新型加密資產的投資，建議提供多樣化投資組合參考。"
        }
    ]

    # 模擬 Agent 輸出文字
    text_lines = []

    for r in latest_records:
        text_lines.append(
            f"👤 使用者: {r['user']}<br>"
            f"📄 問卷名稱: {r['questionnaire']}<br>"
            f"⏰ 完成時間: {r['completed_at']}<br>"
            f"💡 智能分析: {r['analysis']}<br>"
            "────────────────────────────"
        )
    records_text = "<br>".join(text_lines)
    print(records_text,latest_records)
    return {
        "text": f"🧾📢★問卷模塊",
        "extra_data": records_text
    }


def parse_date_range_from_input(user_input):
    """用 GPT 解析使用者輸入的時間範圍，回傳 start_date, end_date"""
    today_str = datetime.today().strftime("%Y-%m-%d")
    prompt = f"""
    你是一個專業的財經助理：
    使用者輸入以下句子，請判斷他想查詢的時間範圍。
    如果說「1M」、「本月」、「過去一個月」、「7D」、「今天」等，請回傳開始與結束日期，
    格式為 YYYY-MM-DD，今天是 {today_str}。
    如果沒有指定時間，請回傳空值。
    輸入句子：{user_input}
    請只用 JSON 格式輸出，例如：{{"start_date": "2025-07-13", "end_date": "2025-08-13"}}
    """
    result = call_chatgpt("時間解析助理", prompt)
    print(user_input, result)
    try:
        data = json.loads(result)

        # 把空字串轉成 None
        start_date = data.get("start_date") or None
        end_date = data.get("end_date") or None

        return start_date, end_date
    except:
        return None, None
    




@csrf_exempt
@require_http_methods(["GET"])
def classify_question_api(request):
    def event_stream():
        # 讀取傳入資料
        data = json.loads(request.GET.get("payload", "{}"))
        user_input = data.get("user_input", "").strip()
        selected_modules = data.get("selected_modules", [])
        yield f'data: {json.dumps({"progress": "loding", "result": {"module": "loding","text": "分析問題中", "data": []}}, ensure_ascii=False)}\n\n'
        # 1️⃣ 分類
        classification_prompt = f"""
        你是一個分類器，幫我判斷下列句子可能屬於哪些類別：
        新聞（news）、價格（price）、其他經濟數據（other）、問卷（questionnaire）。
        可以有多個，請以逗號分隔；如果都不屬於，請回傳 ()。
        輸入句子：{user_input}
        請只輸出分類結果（如：news, price）
        """
        result = call_chatgpt("你是一個精準的分類器", classification_prompt)
        classifications = [c.strip().lower() for c in result.split(",") if c.strip()]
        combined = list(set(selected_modules + classifications))

        module_map = {
            "price": run_price_agent,
            "news": run_news_agent,
            "other": run_other_agent,
            "questionnaire": run_survey_agent
        }
        
        ordered_combined = [k for k in module_map.keys() if k in combined]

        print(ordered_combined)

        # 推送分類結果
        yield f"data: {json.dumps({'classifications': ordered_combined}, ensure_ascii=False)}\n\n"

        # 解析日期
        start_date, end_date = parse_date_range_from_input(user_input)



        # 執行各模組
        final_answers = []

        for module_name in ordered_combined:
            if module_name in module_map:
                # 先推送「生成中」訊息
                yield f'data: {json.dumps({"progress": "loding", "result": {"module": "loding","text": f"{module_name}生成中", "data": []}}, ensure_ascii=False)}\n\n'


                # 執行 module
                answer = module_map[module_name](user_input, start_date, end_date)

                # 整理結果
                if isinstance(answer, dict):
                    final_answers.append({
                        "module": module_name,
                        "text": answer.get("text", ""),
                        "data": answer.get("extra_data", [])
                    })
                else:
                    final_answers.append({
                        "module": module_name,
                        "text": str(answer),
                        "data": []
                    })

                # 每跑完一個模組就推送真正結果
                print({'progress': module_name, 'result': final_answers[-1]})
                yield f"data: {json.dumps({'progress': module_name, 'result': final_answers[-1]}, ensure_ascii=False)}\n\n"


        if not final_answers:
            final_answers.append({
                "module": "none",
                "text": "抱歉，我無法辨識您的問題類型或您未選擇相關模組。",
                "data": []
            })
            yield f"data: {json.dumps({'progress': 'none', 'result': final_answers[-1]}, ensure_ascii=False)}\n\n"

        yield f'data: {json.dumps({"progress": "loding", "result": {"module": "loding","text": "整合回覆中", "data": []}}, ensure_ascii=False)}\n\n'
        # 5️⃣ 整合回覆
        integrated_summary = ""
        try:
            integration_contents = []
            for f in final_answers:
                data_block = f.get('data')
                module_name = f.get('module', 'unknown')
                if isinstance(data_block, list):
                    data_str = "\n".join([str(d) for d in data_block])
                else:
                    data_str = str(data_block)
                integration_contents.append(f"[{module_name} 模塊]\n{data_str}")
            integration_prompt_content = "\n".join(integration_contents)

            integration_prompt = f"""
            使用者問題：{user_input}
            以下是多個不同來源的模塊輸出，請幫我整合成一段自然語言的回覆，
            保留重要數據與事件，邏輯清晰，適合直接回覆使用者：
            {integration_prompt_content}
            """
            integrated_summary = call_chatgpt("你是一個專業的資訊整合助理", integration_prompt)
        except Exception as e:
            integrated_summary = f"⚠️ 整合失敗：{str(e)}"

        # 最後一次推送（整合回覆）
        yield f"data: {json.dumps({'integrated_summary': integrated_summary}, ensure_ascii=False)}\n\n"

        # 可以再補一個完成訊號
        yield "event: end\ndata: done\n\n"

    # SSE 回應
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response



def chat_view(request):
    return render(request, "chat2.html")




