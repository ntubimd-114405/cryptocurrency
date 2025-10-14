import os
import json
import re
from collections import Counter,defaultdict
from decimal import Decimal
from datetime import date,datetime,timedelta, time


import numpy as np
import pandas as pd
import ta
from sklearn.feature_extraction.text import CountVectorizer,ENGLISH_STOP_WORDS


from django.utils import timezone
from django.conf import settings
from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.utils.html import escape
from django.db import IntegrityError
from django.db.models import Min, Max, Sum, DateField
from django.db.models.functions import Cast
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import WeeklyReport,DialogEvaluation
from main.models import CoinHistory,Coin,UserProfile, BitcoinPrice
from news.models import Article
from other.models import FinancialSymbol, FinancialData, Indicator, IndicatorValue, BitcoinMetric, BitcoinMetricData
from agent.models import Questionnaire, Question, AnswerOption, UserAnswer, UserQuestionnaireRecord
from data_analysis.text_generation.chatgpt_api import call_chatgpt
from data_analysis.crypto_ai_agent.news_agent import search_news

from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods




# 1. K線、技術指標數據生成（K線 & TA）-----------
def load_price_data_from_db(coin_id, start_date=None, end_date=None):
    queryset = CoinHistory.objects.filter(coin_id=coin_id)
    name = Coin.objects.get(id=1).coinname

    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)


    queryset = queryset.order_by('-date').values(
        'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
    )[:60*24*120]  # 120天

    df = pd.DataFrame.from_records(queryset)

    if df.empty:
        # 空結果時回傳空值
        return "", pd.DataFrame()

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

    return name, daily_df

# 技術指標計算
def add_technical_indicators(df):
    if df.empty:
        # 建立空 DataFrame，包含後續可能會使用的欄位（空型態）
        empty_df = pd.DataFrame(columns=[
            'rsi', 'macd', 'macd_signal', 'ma20', 'ma60', 
            'Date', 'Date_str', 'Open', 'High', 'Low', 'Close',
            'ohlc', 'rsi_point', 'macd_bar', 'macd_signal_line'
        ])
        return empty_df

    # 計算技術指標
    df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['ma20'] = df['Close'].rolling(window=20).mean()
    df['ma60'] = df['Close'].rolling(window=60).mean()

    # 將日期轉為字串格式供前端使用
    df['Date_str'] = df['Date'].dt.strftime('%Y-%m-%d')

    # 建立畫 K 線圖用欄位格式
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
# -----------1. K線、技術指標數據生成（K線 & TA）


def get_recent_articles(start, end):
    # 假設 start 和 end 是 datetime.date 或 datetime.datetime 物件
    # 如果是日期，轉成 timezone-aware datetime 的區間
    if isinstance(start, (date,)):
        start = timezone.make_aware(datetime.combine(start, datetime.min.time()))
    if isinstance(end, (date,)):
        end = timezone.make_aware(datetime.combine(end, datetime.max.time()))

    articles = Article.objects.filter(time__gte=start, time__lte=end).order_by('-time')
    return articles


# 2. 熱門關鍵詞詞頻統計-----------
def process_word_frequency_sklearn(news_texts, top_n=30, max_features=1000):
    # 自訂停用詞，增加通用無關詞，以免干擾文字雲
    extra_stop_words = {
        's', 'u', 'k', 'its', 'from', 'will', 'be', 'you', 'said', 'about', 'more', 'the',
        'based', 'set', 'up', 'some', 'other', 'any', 'many', 'services', 'receive',
        'story', 'call', 'please', 'in', 'on', 'at', 'by', 'for', 'and', 'or', 'but', 'has',
        'have', 'of', 'to', 'with', 'as', 'is', 'it', 'that', 'this', 'their', 'they', 'them'
        'its', 'from', 'will', 'set', 'you', 'said', 'journalists', 'receive', 'story', 'up',
        'based', 'services', 'be', 'about', 'more', 'million', 'infrastructure', 'platform',
        'coindesk'
    }
    stop_words = list(ENGLISH_STOP_WORDS.union(extra_stop_words))
    
    if isinstance(news_texts, str):
        news_texts = [news_texts]

    if not news_texts or all(not text.strip() for text in news_texts):
        return []

    vectorizer = CountVectorizer(
        stop_words=stop_words,
        max_features=max_features
    )
    word_count_matrix = vectorizer.fit_transform(news_texts)
    feature_names = vectorizer.get_feature_names_out()

    total_counts = word_count_matrix.sum(axis=0).A1

    sorted_indices = total_counts.argsort()[::-1][:top_n]
    keywords = [(feature_names[i], total_counts[i]) for i in sorted_indices]
    results = [(word, int(freq)) for word, freq in keywords]
    return results
# -----------2. 熱門關鍵詞詞頻統計




# Decimal 轉 float

def decimal_to_float(data_list):
    return [float(val) if isinstance(val, Decimal) else val for val in data_list]

# 主視圖：weekly report
def full_month_data_view(start_date=None, end_date=None):
    if end_date is None:
        end_date = timezone.now().date()
    if start_date is None:
        start_date = end_date - timedelta(days=120)

    # 📈 FinancialData 資料
    financial_qs = FinancialData.objects.select_related('symbol').filter(date__range=(start_date, end_date))
    financial_df = pd.DataFrame(list(financial_qs.values(
        'symbol__symbol', 'symbol__name', 'date',
        'open_price', 'high_price', 'low_price', 'close_price', 'volume'
    )))

    # 🧠 IndicatorValue 資料
    indicator_qs = IndicatorValue.objects.select_related('indicator') \
        .order_by('-date')

    # 分組，每個指標取最近 10 筆
    indicator_dict = defaultdict(list)
    for iv in indicator_qs:
        if len(indicator_dict[iv.indicator_id]) < 10:
            indicator_dict[iv.indicator_id].append({
                'indicator__name': iv.indicator.name,
                'indicator__abbreviation': iv.indicator.abbreviation,
                'date': iv.date,
                'value': iv.value
            })

    # 將所有資料合併成 DataFrame
    all_rows = []
    for rows in indicator_dict.values():
        # 每個指標的資料按照日期正序排列
        sorted_rows = sorted(rows, key=lambda x: x['date'])
        all_rows.extend(sorted_rows)

    indicator_df = pd.DataFrame(all_rows)

    # 🔗 BitcoinMetricData 資料
    bitcoin_qs = BitcoinMetricData.objects.select_related('metric').filter(date__range=(start_date, end_date))
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
    reports = WeeklyReport.objects.order_by('-year', '-week')

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


# 3. 週報產生與多模組數據整合-----------
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
    coin,df = load_price_data_from_db(1,start_date,end_date)  # 或 user.id，視你的邏輯
    
    df = add_technical_indicators(df).tail(30)
    ma20_data = decimal_to_float(df['ma20'].tolist())
    ma60_data = decimal_to_float(df['ma60'].tolist())

    news_summary = search_news(
        "BTC",# 目前寫死
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
    )
    news_summary_with_links = ""

    # 先取出所有文章 id
    article_ids = [article_data["id"] for article_data in news_summary]

    # 從資料庫抓對應的 Article 物件
    articles = Article.objects.filter(id__in=article_ids)
    articles_dict = {article.id: article for article in articles}

    # 依照 news_summary 的順序生成 HTML
    for article_data in news_summary:
        article_id = article_data["id"]
        article = articles_dict.get(article_id)

        if not article:
            continue  # 如果資料庫沒有該文章就跳過

        url = reverse('news_detail', kwargs={'article_id': article.id})
        title_html = f'<a href="{url}" target="_blank">{escape(article.title)}</a>'
        date_str = escape(article_data.get("date", ""))
        summary_html = escape(article.summary or "")

    news_summary_with_links = ""

    # 先取出所有文章 id
    article_ids = [int(article_data["id"]) for article_data in news_summary]

    # 從資料庫抓對應的 Article 物件
    articles = Article.objects.filter(id__in=article_ids)
    articles_dict = {article.id: article for article in articles}

    # 依照 news_summary 的順序生成 HTML 並累積文字
    for article_data in news_summary:
        article_id = int(article_data["id"])
        article = articles_dict.get(article_id)
        if not article:
            continue

        # 文章連結
        url = reverse('news_detail', kwargs={'article_id': article.id})
        title_html = f'<a href="{url}" target="_blank">{escape(article.title)}</a>'

        # 日期
        date_str = article.time.strftime("%Y-%m-%d %H:%M") if article.time else escape(article_data.get("date", ""))

        # 文章圖片（小圖）
        article_image_html = ""
        if article.image_url:
            article_image_html = f'<img src="{article.image_url}" alt="Article Image" class="article-image">'

        # 文章摘要
        summary_html = escape(article.summary or "")

        # 情緒分數
        sentiment_html = f'<div class="sentiment-score">情緒分數: {article.sentiment_score:.2f}</div>' if article.sentiment_score else ""

        # 組成新聞卡片 HTML
        news_summary_with_links += f'''
        <div class="news-card">
            <h3>{title_html}</h3>
            <span class="news-date">{date_str}</span>
            <div class="news-body">
                {f'<div class="news-thumb">{article_image_html}</div>' if article_image_html else ''}
                <p class="news-summary">{summary_html}</p>
                {sentiment_html}
            </div>
        </div>
        '''



    # 從資料庫抓取這段時間的文章 content
    start_datetime = datetime.combine(start_date, time.min)  # 00:00:00
    end_datetime   = datetime.combine(end_date, time.max)    # 23:59:59.999999

    # 從資料庫抓文章
    articles_qs = Article.objects.filter(
        time__range=(start_datetime, end_datetime)
    ).values_list('content', flat=True)

    # 過濾 None 或空字串
    news_text_list = [content for content in articles_qs if content]

    # 合併成單一字串給詞頻分析
    news_text = "\n".join(news_text_list)

    # 計算詞頻
    word_freqs = process_word_frequency_sklearn(news_text)

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

        2. 宏觀指標資料（indicator_data_json）：
        {indicator_json[:100]}

        3. 比特幣鏈上指標資料（bitcoin_data_json）：
        {bitcoin_json[:100]}
        """
    ).strip("```").strip("html").strip()
# -----------3. 週報產生與多模組數據整合
    from django.utils import timezone
    import math
    import pandas as pd

    def clean_indicator(value, default=None):
        """
        將指標或資料清理成合法格式，避免 NaN 或 None 傳入 JSONField
        - 可以處理單值 float/int
        - list
        - DataFrame Series
        - list of dict (將 dict 內的 float NaN 轉成 default)
        - dict
        """
        if default is None:
            if isinstance(value, dict):
                default = {}
            elif isinstance(value, list):
                default = []
            else:
                default = 0.0

        if value is None:
            return default

        # DataFrame Series
        if isinstance(value, pd.Series):
            value = value.dropna().tolist()

        # list 處理
        if isinstance(value, list):
            cleaned = []
            for v in value:
                if isinstance(v, dict):
                    new_dict = {}
                    for k, val in v.items():
                        if isinstance(val, float) and math.isnan(val):
                            new_dict[k] = default
                        else:
                            new_dict[k] = val
                    cleaned.append(new_dict)
                elif isinstance(v, float) and math.isnan(v):
                    cleaned.append(default)
                else:
                    cleaned.append(v)
            return cleaned

        # dict 處理
        if isinstance(value, dict):
            new_dict = {}
            for k, val in value.items():
                if isinstance(val, float) and math.isnan(val):
                    new_dict[k] = default
                else:
                    new_dict[k] = val
            return new_dict

        # 單一 float 處理
        if isinstance(value, float) and math.isnan(value):
            return default

        return value

    # 更新或新增 WeeklyReport
    WeeklyReport.objects.update_or_create(
        user=user,
        year=year,
        week=week,
        defaults={
            'start_date': start_date or timezone.now().date(),
            'end_date': end_date or timezone.now().date(),
            'summary': summary or "",
            'news_summary': news_summary_with_links or "",
            'word_frequencies': clean_indicator(word_freqs, {}),
            'ma20_data': clean_indicator(ma20_data, []),
            'ma60_data': clean_indicator(ma60_data, []),
            'ohlc_data': clean_indicator(df.get('ohlc', []), []),
            'rsi_data': clean_indicator(df.get('rsi_point', []), []),
            'macd_data': clean_indicator(df.get('macd_bar', []), []),
            'macd_signal_data': clean_indicator(df.get('macd_signal_line', []), []),
            'coin_analysis': coin_analysis or "",
            'financial_data_json': clean_indicator(financial_json, {}),
            'indicator_data_json': clean_indicator(indicator_json, {}),
            'bitcoin_data_json': clean_indicator(bitcoin_json, {}),
            'long_term_analysis': long_term_analysis or "",
        }
    )

    return redirect('weekly_report_list')



def generate_weekly_report2(year, week):
    today = now().date()
    print(year, week)
    # 根據 year 和 week 計算出 start_date（週一）與 end_date（週日）
    start_date = date.fromisocalendar(year, week, 1)
    end_date = start_date + timedelta(days=6)
    # 如果 end_date 超過今天，改用今天
    if end_date > today:
        end_date = today

    # 重新計算資料
    coin,df = load_price_data_from_db(1,start_date,end_date)  
    

    df = add_technical_indicators(df).tail(30)
    ma20_data = decimal_to_float(df['ma20'].tolist())
    ma60_data = decimal_to_float(df['ma60'].tolist())


    news_summary = search_news(
        "BTC",# 目前寫死
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
    )
    news_summary_with_links = ""

    # 先取出所有文章 id
    article_ids = [article_data["id"] for article_data in news_summary]

    # 從資料庫抓對應的 Article 物件
    articles = Article.objects.filter(id__in=article_ids)
    articles_dict = {article.id: article for article in articles}

    # 依照 news_summary 的順序生成 HTML
    for article_data in news_summary:
        article_id = article_data["id"]
        article = articles_dict.get(article_id)

        if not article:
            continue  # 如果資料庫沒有該文章就跳過

        url = reverse('news_detail', kwargs={'article_id': article.id})
        title_html = f'<a href="{url}" target="_blank">{escape(article.title)}</a>'
        date_str = escape(article_data.get("date", ""))
        summary_html = escape(article.summary or "")

    news_summary_with_links = ""

    # 先取出所有文章 id
    article_ids = [int(article_data["id"]) for article_data in news_summary]

    # 從資料庫抓對應的 Article 物件
    articles = Article.objects.filter(id__in=article_ids)
    articles_dict = {article.id: article for article in articles}

    # 依照 news_summary 的順序生成 HTML 並累積文字
    for article_data in news_summary:
        article_id = int(article_data["id"])
        article = articles_dict.get(article_id)
        if not article:
            continue

        # 文章連結
        url = reverse('news_detail', kwargs={'article_id': article.id})
        title_html = f'<a href="{url}" target="_blank">{escape(article.title)}</a>'

        # 日期
        date_str = article.time.strftime("%Y-%m-%d %H:%M") if article.time else escape(article_data.get("date", ""))

        # 文章圖片（小圖）
        article_image_html = ""
        if article.image_url:
            article_image_html = f'<img src="{article.image_url}" alt="Article Image" class="article-image">'

        # 文章摘要
        summary_html = escape(article.summary or "")

        # 情緒分數
        sentiment_html = f'<div class="sentiment-score">情緒分數: {article.sentiment_score:.2f}</div>' if article.sentiment_score else ""

        # 組成新聞卡片 HTML
        news_summary_with_links += f'''
        <div class="news-card">
            <h3>{title_html}</h3>
            <span class="news-date">{date_str}</span>
            <div class="news-body">
                {f'<div class="news-thumb">{article_image_html}</div>' if article_image_html else ''}
                <p class="news-summary">{summary_html}</p>
                {sentiment_html}
            </div>
        </div>
        '''



    # 從資料庫抓取這段時間的文章 content
    start_datetime = datetime.combine(start_date, time.min)  # 00:00:00
    end_datetime   = datetime.combine(end_date, time.max)    # 23:59:59.999999

    # 從資料庫抓文章
    articles_qs = Article.objects.filter(
        time__range=(start_datetime, end_datetime)
    ).values_list('content', flat=True)

    # 過濾 None 或空字串
    news_text_list = [content for content in articles_qs if content]

    # 合併成單一字串給詞頻分析
    news_text = "\n".join(news_text_list)

    # 計算詞頻
    word_freqs = process_word_frequency_sklearn(news_text)

    # 統計有 sentiment_score 的文章數，分中立、正面、負面
    sentiment_counts = {
        'positive': 0,  # 例如 sentiment_score > 0.6
        'neutral': 0,   # sentiment_score介於0.4~0.6
        'negative': 0   # sentiment_score < 0.4
    }

    for article in articles_qs:
        score = article['sentiment_score']
        if score is not None:
            if score > 0.1:
                sentiment_counts['positive'] += 1
            elif score < -0.1:
                sentiment_counts['negative'] += 1
            else:
                sentiment_counts['neutral'] += 1

    sentiment_counts_json = json.dumps(sentiment_counts, ensure_ascii=False)
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
    

    # 📊 中長期觀點資料整合
    monthly_data = full_month_data_view(start_date,end_date)
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

        2. 宏觀指標資料（indicator_data_json）：
        {indicator_json[:100]}

        3. 比特幣鏈上指標資料（bitcoin_data_json）：
        {bitcoin_json[:100]}
        """
    ).strip("```").strip("html").strip()

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

        3. 近期新聞情緒分類數據：
        {sentiment_counts}
        
        4. 長期市場觀察：
        {long_term_analysis}
        """
    ).strip("```").strip("html").strip()
# -----------3. 週報產生與多模組數據整合
    from django.utils import timezone
    import math
    import pandas as pd

    def clean_indicator(value, default=None):
        """
        將指標或資料清理成合法格式，避免 NaN 或 None 傳入 JSONField
        - 可以處理單值 float/int
        - list
        - DataFrame Series
        - list of dict (將 dict 內的 float NaN 轉成 default)
        - dict
        """
        if default is None:
            if isinstance(value, dict):
                default = {}
            elif isinstance(value, list):
                default = []
            else:
                default = 0.0

        if value is None:
            return default

        # DataFrame Series
        if isinstance(value, pd.Series):
            value = value.dropna().tolist()

        # list 處理
        if isinstance(value, list):
            cleaned = []
            for v in value:
                if isinstance(v, dict):
                    new_dict = {}
                    for k, val in v.items():
                        if isinstance(val, float) and math.isnan(val):
                            new_dict[k] = default
                        else:
                            new_dict[k] = val
                    cleaned.append(new_dict)
                elif isinstance(v, float) and math.isnan(v):
                    cleaned.append(default)
                else:
                    cleaned.append(v)
            return cleaned

        # dict 處理
        if isinstance(value, dict):
            new_dict = {}
            for k, val in value.items():
                if isinstance(val, float) and math.isnan(val):
                    new_dict[k] = default
                else:
                    new_dict[k] = val
            return new_dict

        # 單一 float 處理
        if isinstance(value, float) and math.isnan(value):
            return default

        return value

    # 更新或新增 WeeklyReport
    WeeklyReport.objects.update_or_create(
        year=year,
        week=week,
        defaults={
            'start_date': start_date or timezone.now().date(),
            'end_date': end_date or timezone.now().date(),
            'summary': summary or "",
            'news_summary': news_summary_with_links or "",
            'word_frequencies': clean_indicator(word_freqs, {}),
            'ma20_data': clean_indicator(ma20_data, []),
            'ma60_data': clean_indicator(ma60_data, []),
            'ohlc_data': clean_indicator(df.get('ohlc', []), []),
            'rsi_data': clean_indicator(df.get('rsi_point', []), []),
            'macd_data': clean_indicator(df.get('macd_bar', []), []),
            'macd_signal_data': clean_indicator(df.get('macd_signal_line', []), []),
            'coin_analysis': coin_analysis or "",
            'financial_data_json': clean_indicator(financial_json, {}),
            'indicator_data_json': clean_indicator(indicator_json, {}),
            'bitcoin_data_json': clean_indicator(bitcoin_json, {}),
            'long_term_analysis': long_term_analysis or "",
            'sentiment_counts_json': sentiment_counts_json,  # 新增欄位存JSON
        }
    )





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
    report = get_object_or_404(WeeklyReport, id=report_id)

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
        'sentiment_counts_json': json.dumps(report.sentiment_counts_json),
        'year': report.year,
        'week': report.week,
        'start_date': report.start_date,
        'end_date': report.end_date,
        'created_at': report.created_at,
        'watchlist': my_favorite_coins_view(request),  # <-- 加入這行
    }

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




def parse_safe_date(date_str):
    """將字串轉成 date，失敗回傳 None"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None
    
# 5. 各類智能分析小模組（價格、新聞、其他數據、問卷）-----------
# 價格分析模組
def run_price_agent(user, user_input, start_date=None, end_date=None):
    coin_symbol = parse_coin_from_input(user_input)
    # 確認幣種存在
    if not Coin.objects.filter(abbreviation=coin_symbol).exists():
        return {"text": f"⚠️ 抱歉，系統內沒有找到 {coin_symbol} 的資料。", "extra_data": [],"analyze" : ""}

    qs = CoinHistory.objects.filter(coin__abbreviation=coin_symbol)
    if not qs.exists():
        return {"text": f"⚠️ 模組 price 執行失敗：{coin_symbol} 暫無資料", "extra_data": [],"analyze" : ""}

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
            return {"text": f"⚠️ 模組 price 執行失敗：{coin_symbol} 暫無資料", "extra_data": [],"analyze" : ""}
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
        return {"text": f"⚠️ 模組 price 執行失敗：{coin_symbol} 在 {start_date} 至 {end_date} 之間沒有資料", "extra_data": [],"analyze" : ""}

    # 生成 prompt
    analysis_prompt = f"""
    你是一個專業加密貨幣分析師。請幫我分析以下比特幣交易數據：
    {results}

    請分析每一天的價格走勢（開盤、收盤、最高、最低）、交易量變化，以及整體趨勢特徵。
    請提供：
    1. 價格趨勢分析（上升、下降、盤整）
    2. 交易量變化趨勢
    3. 總體觀察與短期預測
    請用簡明扼要的文字列出。
    """

    analyze = call_chatgpt("比特幣價格分析師", analysis_prompt).replace("\n", "<br>")

    return {"text": f"💰★價格模塊", "extra_data": results,"analyze" : analyze}

# 新聞模組
def run_news_agent(user, user_input, start_date=None, end_date=None):

    """
    搜尋新聞並直接將標題轉換為可點擊連結 (news_detail)，
    並換行處理輸出 HTML
    """
    translated = call_chatgpt(
    "翻譯助手",
    f"請將以下中文翻譯成英文：\n{user_input}"
    )
    # 取得新聞資料 (list)
    news_summary = search_news(
        question=translated,
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
            d=item.get("date")
            try:
                url = reverse('news_detail', kwargs={'article_id': article_id})
                title_html = f'<a href="{url}" target="_blank">{title}</a>'
            except:
                title_html = title
            text_parts.append(f"<b>{title_html}</b><br><b>{d}</b><br>{summary}")
        return "<br><br>".join(text_parts)

    news_summary_with_links = convert_and_link(news_summary)
    analysis_prompt = f"""
    你是一位專業新聞分析師。請幫我分析以下新聞內容：
    {news_summary}

    請提供：
    1. 新聞的主要事件或主題
    2. 每則新聞的重要資訊摘要
    3. 對加密貨幣市場可能的影響（若有）
    """

    analyze = call_chatgpt("新聞分析師", analysis_prompt).replace("\n", "<br>")

    return {
        "text": "📰★新聞模塊",
        "extra_data": news_summary_with_links,
        "analyze" : analyze
    }

# 經濟/區塊鏈其他數據模組
def run_other_agent(user, user_input, start_date=None, end_date=None):
    if end_date is None:
        end_date = datetime.now().date()

    # FinancialData - 折線圖用 close_price
    financial_data_sample = []
    symbols = FinancialSymbol.objects.all()[:1]
    for symbol in symbols:
        data_qs = symbol.financial_data.filter(
            date__lte=end_date
        ).order_by('-date')[:7]
        for d in data_qs:
            financial_data_sample.append({
                "symbol": symbol.name,
                "date": d.date.isoformat(),  # 用字串
                "value": d.close_price       # 折線圖用值
            })

    # IndicatorValue - 折線圖用 value
    indicator_data_sample = []
    indicators = Indicator.objects.all()[:1]
    for indicator in indicators:
        data_qs = IndicatorValue.objects.filter(
            indicator=indicator,
            date__lte=end_date
        ).order_by('-date')[:7]
        for d in data_qs:
            indicator_data_sample.append({
                "indicator": indicator.name,
                "date": d.date.isoformat(),
                "value": d.value
            })

    # 合併到 extra_data，保留分類
    extra_data = {
        "financial_data": financial_data_sample,
        "indicator_data": indicator_data_sample,
    }

    # 生成 prompt
    analysis_prompt = f"""
        你是一位專業加密貨幣與經濟分析師，請利用以下數據：
        {extra_data}

        請提供簡短結論。並根據使用者問題「{user_input}」回答，使分析更貼切其需求。
        """

    analyze = call_chatgpt("分析師", analysis_prompt).replace("\n", "<br>")

    return {
        "text": "📊★其他經濟數據折線圖資料",
        "extra_data": extra_data,
        "analyze": analyze
    }

RISK_QUESTIONNAIRE_IDS = [2, 3, 4, 9]

# 問卷模組
def run_survey_agent(user, user_input, start_date=None, end_date=None): 

    if user.is_authenticated:
        # 取得使用者的問卷風險分析
        user_answers = UserAnswer.objects.filter(
            user=user,
        ).prefetch_related("selected_options")
        total_score = 0
        answer_count = 0
        for ans in user_answers:
            for option in ans.selected_options.all():
                q_order = ans.question.questionnaire.id
                if q_order in RISK_QUESTIONNAIRE_IDS:
                    total_score += option.score
                    answer_count += 1

        if answer_count == 0:
            link = reverse('agent:questionnaire_list')
            return {
            "text": f"🧾📢★問卷模塊",
            "extra_data": f'<a href="{link}" target="_blank">請先填寫問卷頁面(填問卷編號2、3、4、9能更準確判斷)</a>',
            "analyze": "使用者沒有填寫問卷，無法判斷屬性"
            }
        else:
            average = total_score / answer_count

            # allocation 與風險屬性判斷
            ratio = min(max(average / 5, 0), 1)
            allocation = {
                "穩定幣": 0.6 * (1 - ratio),
                "主流幣": 0.3,
                "成長幣": 0.1 + 0.3 * ratio,
                "迷因幣": 0.0 + 0.2 * ratio,
            }
            total = sum(allocation.values())
            allocation = {k: round(v/total, 2) for k, v in allocation.items()}

            if average <= 2.5:
                risk_type = "保守型"
            elif average <= 4:
                risk_type = "穩健型"
            else:
                risk_type = "積極型"
            allocation_text = "<br>".join([f"・{k}：{v*100:.0f}%" for k, v in allocation.items()])

            link = reverse('agent:analysis_result_view')

            records_text = (
                f"📊 <b>您的投資風險屬性：</b><span style='color:blue'>{risk_type}</span><br>"
                f"📈 <b>問卷平均分數：</b>{average:.2f} 分<br><br>"
                f"💡 <b>建議資產配置：</b><br>{allocation_text}<br><br>"
                f'<a href="{link}" target="_blank">查看更多</a>'
            )

        return {
            "text": f"🧾📢★問卷模塊",
            "extra_data": records_text,
            "analyze": records_text
        }
    else:
        link = reverse('login')
        return {
            "text": f"🧾📢★問卷模塊",
            "extra_data": f'<a href="{link}">請先登入，以取得更準確的判斷</a>',
            "analyze": "使用者沒有登入，無法判斷屬性"
            }
# -----------5.各類智能分析小模組（價格、新聞、其他數據、問卷）


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
    



# 4. 智能對話/模組分類與多源數據SSE串流回覆-----------
@csrf_exempt
@require_http_methods(["GET"])
def classify_question_api(request):
    def event_stream():
        # 讀取傳入資料
        data = json.loads(request.GET.get("payload", "{}"))
        user_input = data.get("user_input", "").strip()
        selected_modules = data.get("selected_modules", [])
        user = request.user
        yield f'data: {json.dumps({"progress": "loding", "result": {"module": "loding","text": "分析問題中", "data": []}}, ensure_ascii=False)}\n\n'
        # 1️⃣ 分類
        classification_prompt = f"""
        你是一個精準的分類器，請判斷下列句子屬於哪些類別：
        - 新聞（news）：內容涉及近期事件、時事、政策、公告或市場動態。
        - 加密貨幣價格（price）：內容與加密貨幣、代幣或市場價格、行情、變化相關。
        - 其他經濟數據（other）：內容需要更多市場、金融或經濟相關資料作為背景或分析依據。
        - 問卷（questionnaire）：使用者表達個人意圖、需求、投資建議或偏好（如需要幫忙推薦、分析、建議）。

        判斷邏輯：
        - 只要句子包含「加密貨幣」、「比特幣」等關鍵字，或者提到加密貨幣名稱，請務必標示price。
        - 若句子涉及近期事件、消息、市場公告，包含news。
        - 若需查找及分析額外資料（非價格或新聞），包含other。
        - 表達個人需求、投資建議則包含questionnaire。
        - 若皆不符，回傳 ()。

        範例：
        輸入：我想查比特幣價格 → price
        輸入：9月的比特幣行情怎麼樣？ → price
        輸入：請給我其他相關數據 → price, other
        輸入：最近比特幣有什麼消息？ → news
        輸入：我想要投資建議 → questionnaire
        輸入：這是無關內容 → ()

        請只輸出分類結果（如：news, price）。

        輸入句子：{user_input}
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



        # 推送分類結果
        yield f"data: {json.dumps({'classifications': ordered_combined}, ensure_ascii=False)}\n\n"
        final_answers = []
        if ordered_combined:
        # 解析日期
            start_date, end_date = parse_date_range_from_input(user_input)


            # 執行各模組
            for module_name in ordered_combined:
                if module_name in module_map:
                    # 先推送「生成中」訊息
                    yield f'data: {json.dumps({"progress": "loding", "result": {"module": "loding","text": f"{module_name}生成中", "data": []}}, ensure_ascii=False)}\n\n'


                    # 執行 module
                    answer = module_map[module_name](user,user_input, start_date, end_date)

                    # 整理結果
                    if isinstance(answer, dict):
                        final_answers.append({
                            "module": module_name,
                            "text": answer.get("text", ""),
                            "data": answer.get("extra_data", []),
                            "analyze" : answer.get("analyze", ""),
                        })
                    else:
                        final_answers.append({
                            "module": module_name,
                            "text": str(answer),
                            "analyze" : ""
                        })
                    # 每跑完一個模組就推送真正結果
                    yield f"data: {json.dumps({'progress': module_name, 'result': final_answers[-1]}, ensure_ascii=False)}\n\n"


        if not final_answers:
            final_answers.append({
                "module": "none",
                "text": ("抱歉，我無法理解您的問題或未能識別相關模組。"
                        "請確認您的提問內容是否完整，或嘗試重新描述您的需求。謝謝！<br>"
                        "使用說明：<br>"
                        "1. 請直接輸入您的問題或需求。<br>"
                        "2. 可選擇適合的模組以獲得更精準的協助，如新聞查詢、價格查詢、經濟數據分析等。<br>"
                        "3. 若不確定，請簡單描述您的問題，我們會嘗試自動判斷所需模組。"),
                "data": []
            })
            yield f"data: {json.dumps({'progress': 'none', 'result': final_answers[-1]}, ensure_ascii=False)}\n\n"

        # 5️⃣ 整合回覆
        yield f'data: {json.dumps({"progress": "loding", "result": {"module": "loding","text": "整合回覆中", "data": []}}, ensure_ascii=False)}\n\n'
        integrated_summary = ""
        try:
            integration_contents = []
            for f in final_answers:
                data_block = f.get('analyze')
                module_name = f.get('module', 'unknown')
                if isinstance(data_block, list):
                    data_str = "\n".join([str(d) for d in data_block])
                else:
                    data_str = str(data_block)
                integration_contents.append(f"[{module_name} 模塊]\n{data_str}")
            integration_prompt_content = "\n".join(integration_contents)

            integration_prompt = f"""
            使用者問題：{user_input}
            以下是多個不同來源的模塊輸出，請幫我整合成條列式的自然語言的回覆，
            保留重要數據與事件，邏輯清晰，適合直接回覆使用者，並在最後回答使用者的問題：
            {integration_prompt_content}
            
            """
            integrated_summary = call_chatgpt("你是一個專業的資訊整合助理", integration_prompt)
        except Exception as e:
            integrated_summary = f"⚠️ 整合失敗：{str(e)}"

        # 最後一次推送（整合回覆）
        yield f"data: {json.dumps({'integrated_summary': integrated_summary}, ensure_ascii=False)}\n\n"

        DialogEvaluation.objects.create(
            user_input=user_input,
            expected_intent="(人工)認為這句話應該屬於哪種意圖（標準答案）",  # 也可改成更精確的意圖
            predicted_intent=", ".join(ordered_combined) + (f", {start_date} ~ {end_date}" if start_date and end_date else ""),
            expected_response="(人工)認為合適的機器人回應",
            generated_response=integrated_summary,
            analyze_data=json.dumps([fa.get("analyze", "") for fa in final_answers], ensure_ascii=False),  # 這一行存所有 analyze
            task_success=True  # 若有實際成功判斷條件可替換
        )
        # 可以再補一個完成訊號
        yield "event: end\ndata: done\n\n"

    # SSE 回應
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response
# -----------4. 智能對話/模組分類與多源數據SSE串流回覆


def chat_view(request):
    return render(request, "chat2.html")



@csrf_exempt
@require_http_methods(["GET"])
def get_module_suggestions_api(request):
    """
    根據使用者選擇的模組回傳推薦問題列表
    """
    selected_modules = request.GET.getlist("modules[]", [])

    # 各模組對應建議
    suggestions = {
        "price": [
            "目前比特幣價格分析",
            "以太坊技術指標與走勢",
            "加密貨幣市場漲跌原因",
        ],
        "news": [
            "最近加密貨幣新聞重點",
            "比特幣相關政策更新",
            "最新市場公告與事件",
        ],
        "other": [
            "台股與美股的相關性",
            "美元指數對市場的影響",
            "通膨數據與加密貨幣關係",
        ],
        "questionnaire": [
            "請根據問卷結果給我投資建議",
            "幫我推薦適合的投資標的",
            "分析我目前的投資偏好",
        ]
    }

    # ✅ 若使用者沒有勾選模組 → 給「綜合建議」
    if not selected_modules:
        merged_suggestions = [
            "目前比特幣價格分析",
            "給我九月的乙太坊價格，並給我新聞跟相關數據，並給我投資建議",
            "最近加密貨幣新聞重點",
        ]
    else:
        #測試使用，未來可以使用註解的版本
        merged_suggestions = [ 
            "目前比特幣價格分析",
            "給我九月的乙太坊價格，並給我新聞跟相關數據，並給我投資建議",
            "最近加密貨幣新聞重點",
        ]
        '''
        # 整合使用者選擇模組的建議
        merged_suggestions = []
        for module in selected_modules:
            merged_suggestions.extend(suggestions.get(module, []))
        '''
    return JsonResponse({"suggestions": merged_suggestions}, json_dumps_params={"ensure_ascii": False})
