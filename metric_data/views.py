from django.shortcuts import render
from .models import BitcoinMetric, BitcoinMetricData
from django.core.serializers.json import DjangoJSONEncoder
import json

def metric_home(request):
    # 獲取所有比特幣指標
    metrics = BitcoinMetric.objects.all()

    context = {
        'metrics': metrics
    }
    return render(request, 'metric_home.html', context)


def charts_view(request):
    # 取得所有 Bitcoin Metric 及其對應的數據
    metrics = BitcoinMetric.objects.all()
    chart_data = {}

    for metric in metrics:
        # 依日期排序
        values = BitcoinMetricData.objects.filter(metric=metric).order_by('date')
        dates = [value.date.strftime("%Y-%m-%d") for value in values]
        data = [value.value for value in values]
        chart_data[metric.name] = {
            'dates': dates,
            'data': data,
        }
    
    context = {
        'chart_data': json.dumps(chart_data, cls=DjangoJSONEncoder)
    }
    return render(request, 'metric_charts.html', context)
