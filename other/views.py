from django.shortcuts import render
from .models import FinancialSymbol, FinancialData, Indicator, IndicatorValue, BitcoinMetric, BitcoinMetricData, TrendData
from django.core.serializers.json import DjangoJSONEncoder
import json


def home(request):

    context = {

    }
    return render(request, 'other_home.html', context)

# 1. 金融市場數據總覽（finance_chart）-----------
def finance_chart(request):
    # 取得所有金融符號及其對應的數據
    metrics = FinancialSymbol.objects.all()
    chart_data = {}

    for metric in metrics:
        # 依日期排序
        values = FinancialData.objects.filter(symbol=metric).order_by('date')
        dates = [value.date.strftime("%Y-%m-%d") for value in values]
        data = [value.close_price for value in values]  # 使用 close_price 属性
        chart_data[metric.name] = {  # 使用 name 作為鍵
            'dates': dates,
            'data': data,
        }
    
    context = {
        'chart_data': json.dumps(chart_data, cls=DjangoJSONEncoder)
    }
    return render(request, 'finance_charts.html', context)
# -----------1. 金融市場數據總覽（finance_chart）



# 2. 宏觀經濟指標動態圖（macro_chart）-----------
def macro_chart(request):
    # 取得所有 Indicator 及其對應的 IndicatorValue
    indicators = Indicator.objects.all()
    chart_data = {}

    for indicator in indicators:
        # 依日期排序
        values = IndicatorValue.objects.filter(indicator=indicator).order_by('date')
        dates = [iv.date.strftime("%Y-%m-%d") for iv in values]
        data = [iv.value for iv in values]
        chart_data[indicator.name] = {
            'dates': dates,
            'data': data,
        }
    
    context = {
        'chart_data': json.dumps(chart_data, cls=DjangoJSONEncoder)
    }
    return render(request, 'macro_charts.html', context)
# -----------2. 宏觀經濟指標動態圖（macro_chart）

# 3. 比特幣鏈上指標展示（metric_chart）-----------
def metric_chart(request):
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
# -----------3. 比特幣鏈上指標展示（metric_chart）


# 4. 幣種/趨勢類數據視覺化（trend_data_chart）-----------
def trend_data_chart(request):
    trend_data = TrendData.objects.filter(coin_id=1).order_by('date')
    
    dates = [td.date.strftime("%Y-%m-%d") for td in trend_data]
    full_values = [td.full_value for td in trend_data]
    abbreviated_values = [td.abbreviated_value for td in trend_data]
    
    chart_data = {
        'dates': dates,
        'full_values': full_values,
        'abbreviated_values': abbreviated_values
    }
    
    context = {
        'chart_data': json.dumps(chart_data, cls=DjangoJSONEncoder)
    }
    return render(request, 'trend_data_charts.html', context)
# -----------4. 幣種/趨勢類數據視覺化（trend_data_chart）
