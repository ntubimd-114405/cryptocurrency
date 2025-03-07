from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='other_home'),  # 將路徑連結到視圖
    path('finance_chart/', finance_chart, name='finance_chart'),
    path('macro_chart/', macro_chart, name='macro_chart'),
    path('metric_chart/', metric_chart, name='metric_chart'),
    path('trend-data-chart/', trend_data_chart, name='trend_data_chart'),
]