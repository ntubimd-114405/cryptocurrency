from django.urls import path
from .views import *

urlpatterns = [
    path('', finance_home, name='finance_home'),  # 將路徑連結到視圖
    path('finance_chart/', charts_view, name='finance_chart'),
]