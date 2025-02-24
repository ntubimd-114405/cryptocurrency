from django.urls import path
from .views import *

urlpatterns = [
    path('', metric_home, name='metric_home'),  # 將路徑連結到視圖
    path('metric_chart/', charts_view, name='metric_chart'),
]