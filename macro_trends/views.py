from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Indicator, IndicatorValue

def charts_view(request):
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
    return render(request, 'charts.html', context)
