from django.urls import path
from .views import *

urlpatterns = [
    path('', macro_home, name='macro_home'),  # 將路徑連結到視圖
    path('charts/', charts_view, name='macro_charts'),
]