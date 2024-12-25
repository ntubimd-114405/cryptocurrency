from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),  # 將路徑連結到視圖
    path('crypto/', views.crypto_list, name='crypto_list'),  # 用於展示虛擬貨幣價格的列表頁面（假設已經設置）
    path('crypto/<int:pk>/', views.crypto_detail, name='crypto_detail'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user_profile/', views.upload_profile_image, name='user_profile'),
    path('update_notification_preferences/', views.update_notification_preferences, name='update_notification_preferences'),
    path('add_to_favorites/<int:pk>/', views.add_to_favorites, name='add_to_favorites'),
    path('remove-favorite/<int:pk>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('favorites/', views.favorite_coins, name='favorite_coins'),
    path('news/', views.news_list, name='news_list'),
    path('coin_history/<int:coin_id>/', views.coin_history, name='coin_history'),
    path('post/', views.X_list, name='X_list'),
    path('register/', views.register_view, name='register'),
    path('news/<int:article_id>/', views.news_detail, name='news_detail'),

    # 忘記密碼
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('update_password/', views.update_password, name='update_password'),
    path('update-firstname/', views.update_firstname, name='update_firstname'),

    path('send-email/', views.send_email_news, name='send_email'),



]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


