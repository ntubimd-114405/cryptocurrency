from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='news_home'),  # 將路徑連結到視圖
    path('list/', news_list, name='news_list'),
    path('detail/<int:article_id>/', news_detail, name='news_detail'),
]

