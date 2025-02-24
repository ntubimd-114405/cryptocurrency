from datetime import datetime, timezone,timedelta
from celery import shared_task

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
        
        # 利用 update_or_create 確保資料庫中存在「Hash Rate」這個指標
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