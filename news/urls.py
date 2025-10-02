from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('', news_home, name='news_home'),  # 將路徑連結到視圖
    path('list/', news_list, name='news_list'),
    path('detail/<int:article_id>/', news_detail, name='news_detail'),
    path('post/', views.X_list, name='X_list'),
    path('api/search-news/', views.search_news_api, name='search_news_api'),
    path('search-news/', views.search_news_page, name='search_news_page'),
]

