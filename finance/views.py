from django.shortcuts import render
from .models import FinancialSymbol, FinancialData  # 假设 FinancialData 模型已存在
from django.core.serializers.json import DjangoJSONEncoder
import json

def finance_home(request):
    # 獲取所有金融指標
    symbols = FinancialSymbol.objects.all()

    context = {
        'symbols': symbols
    }
    return render(request, 'finance_home.html', context)


def charts_view(request):
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
