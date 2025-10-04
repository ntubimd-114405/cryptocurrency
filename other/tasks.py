from celery import shared_task
from datetime import datetime, timezone, timedelta
from django.utils.timezone import now
import pandas as pd
from django.utils import timezone as tz

@shared_task
def fetch_trends_task():
    from .models import TrendData
    from main.models import Coin  # 引入 Coin 模型
    from data_collector.google_trends.api import trends
    
    try:
        coin = Coin.objects.get(pk=1)
    except Coin.DoesNotExist:
        return "找不到 id=1 的 Coin 資料"

    # 查找最新的趨勢資料時間
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)

    end = now()
    timeframe = f"{start.strftime('%Y-%m-%d')} {end.strftime('%Y-%m-%d')}"
    data = trends(timeframe)
    for index, row in data.iterrows():
        
        date = str(row['date']) + "+00:00" # 確保 date 是帶時區的 datetime 對象
        full_value = int(row['full_value'])
        abbreviated_value = int(row['abbreviated_value'])
        trend_data, created = TrendData.objects.update_or_create(
            coin=coin,
            date=date,
            defaults={
                'full_value': full_value,
                'abbreviated_value': abbreviated_value,
            }
        )
    print(f"成功儲存 {coin.coinname} Google Trends 資料")


# 8-1 抓取金融資料
@shared_task
def save_financial():
    from data_collector.fin.financial_data import get_finance
    from .models import FinancialSymbol, FinancialData
    symbols = {
        "S&P 500 指數": "^GSPC",   # S&P500 指數
        "黃金期貨": "GC=F",         # 黃金期貨
        "WTI 原油期貨": "CL=F",     # WTI 原油期貨
        "美元指數": "DX-Y.NYB",    # 美元指數
        "VIX波動率指數": "^VIX", 
    }

    for name, sym in symbols.items():
        # 確保 FinancialSymbol 存在
        financial_symbol, created = FinancialSymbol.objects.get_or_create(
            symbol=sym,
            defaults={'name': name}
        )

        # 找到 FinancialData 最後的日期
        last_data = FinancialData.objects.filter(symbol=financial_symbol).order_by('date').last()
        if last_data:
            start_date = datetime.combine(last_data.date, datetime.min.time(), tzinfo=timezone.utc) + tz.timedelta(days=1)
        else:
            start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)

        # 獲取金融數據
        data = get_finance(sym, start_date)
# 8-3 儲存或更新 FinancialData
        if data is not None:
            for index, row in data.iterrows():
                FinancialData.objects.update_or_create(
                    symbol=financial_symbol,
                    date=index.date(),  # 使用索引中的日期
                    defaults={
                        'open_price': float(row['Open'].iloc[0]),  # 使用 .iloc[0]
                        'high_price': float(row['High'].iloc[0]),
                        'low_price': float(row['Low'].iloc[0]),
                        'close_price': float(row['Close'].iloc[0]),
                        'volume': int(row['Volume'].iloc[0]),      # 使用 .iloc[0]
                    }
                )
            print(f"{financial_symbol}更新{len(data)}筆")
        else:
            print(f"{financial_symbol}更新0筆")

#9-1 更新比特幣相關指標
@shared_task
def update_bitcoin_metrics():
    from .models import BitcoinMetric, BitcoinMetricData
    from data_collector.btc_related.btc_data import get_all_data
    from django.db.models import Max

    names_to_add = ['Hash Rate',"Number Of Unique Addresses Used","Average Block Size","Miners Revenue","Mempool Size","Difficulty"]
    # 遍歷陣列，將每個 name 加入到 BitcoinMetric
    for name in names_to_add:
        # 嘗試創建 BitcoinMetric 實例，如果已經存在則忽略
        BitcoinMetric.objects.get_or_create(name=name)
    # 獲取每個 BitcoinMetric 的最新 BitcoinMetricData 時間
    latest_data = (
        BitcoinMetric.objects
        .annotate(latest_date=Max('data__date'))  # 使用 annotate 來獲取每個 metric 的最新 date
    )

    # 迭代 latest_data，獲取每個 BitcoinMetric 及其最新的時間
    for metric in latest_data:
        # 獲取新的 Bitcoin hash rate 數據
        if metric.latest_date:
            start_date = metric.latest_date + timedelta(seconds=1)
        else:
            start_date = datetime(2020, 1, 1)  # 指定默認日期

        # 獲取新的 Bitcoin hash rate 數據
        data = get_all_data(metric.name, start_date.isoformat())
        
# 9-3利用 update_or_create 確保資料庫中存在「Hash Rate」這個指標
        metric, created = BitcoinMetric.objects.update_or_create(
            name=data["name"],
            defaults={
                "unit": data["unit"],
                "period": data["period"],
                "description": data["description"]
            }
        )

        # 儲存時間序列數據
        new_entries_count = 0  # 初始化新增計數器
        for timestamp, value in data["values"]:
            timestamp = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)

            if value is not None:
                # 嘗試獲取或創建 BitcoinMetricData
                obj, created_data = BitcoinMetricData.objects.get_or_create(
                    metric=metric,
                    date=timestamp,
                    defaults={"value": value}
                )
                if created_data:  # 如果創建了新的實例
                    new_entries_count += 1  # 增加計數器

        print(f"{data['name']} 數據更新完成，新增數據條目數：{new_entries_count}")

# 10-1 更新宏觀經濟指標
@shared_task
def macro_economy():
    from .models import Indicator,IndicatorValue
    from data_collector.macro_economy.fredapi_data import get_fred_data
    indicators = {
        "國內生產總值 (GDP)": "GDP",
        "失業率": "UNRATE",
        "通脹率 (CPI)": "CPIAUCSL",
        "利率 (聯邦基金利率)": "FEDFUNDS",
        "貿易平衡": "NETEXP",
        "貨幣供應量 (M2)": "M2SL",
        "政府預算赤字/盈餘": "FYFSD",
        "生產者物價指數 (PPI)": "PPIACO",
        "消費者信心指數 (CCI)": "UMCSENT",
        "金融壓力指數(FSI)":"STLFSI4",
        "經濟政策不確定性指數(EPU)":"USEPUINDXD",
        "美國外匯儲備":"TRESEGUSM052N",
        "美國聯邦政府總債務":"GFDEBTN",
        "美國房價指數":"CSUSHPISA",
        "家庭債務占個人收入百分比":"TDSP",
        "美國家庭債務佔GDP百分比":"HDTGPDUSQ163N",
    }

    for k, v in indicators.items():     
        indicator, created = Indicator.objects.update_or_create(
            abbreviation=v,
            defaults={'name': k}  # 如果已存在，則更新 name
        )
              
        data = get_fred_data(v) 

# 10-3 儲存或更新 IndicatorValue
        for date, value in data.items():  
            date = date.date() 
            if pd.notna(value):
                IndicatorValue.objects.get_or_create(
                    indicator=indicator, date=date, defaults={'value': value}
                )

        print(f"{k} 完成處理")


def all():
    fetch_trends_task()
    save_financial()
    update_bitcoin_metrics()
    macro_economy()