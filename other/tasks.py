from celery import shared_task
from datetime import datetime, timezone, timedelta
from django.utils.timezone import now
import pandas as pd

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

    return f"成功儲存 {coin.coinname} Google Trends 資料"
