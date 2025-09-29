from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import track_impression

urlpatterns = [
    path('', views.home, name='home'),  # 將路徑連結到視圖
    path('crypto/', views.crypto_list, name='crypto_list'),  # 用於展示虛擬貨幣價格的列表頁面（假設已經設置）
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user_profile/', views.upload_profile_image, name='user_profile'),
    path('update_notification_preferences/', views.update_notification_preferences, name='update_notification_preferences'),
    path('add_to_favorites/<int:pk>/', views.add_to_favorites, name='add_to_favorites'),
    path('remove-favorite/<int:pk>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('favorites/', views.favorite_coins, name='favorite_coins'),
    path('register/', views.register_view, name='register'),
    path('crypto_prices_ajax/', views.crypto_prices_ajax, name='crypto_prices_ajax'),
    path('submit/', views.submit_questionnaire, name='submit_questionnaire'),
    path('api/track_impression/', track_impression),
    

    # 忘記密碼
    # path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    # path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('update_password/', views.update_password, name='update_password'),
    path('update-firstname/', views.update_firstname, name='update_firstname'),

    path('send-email/', views.send_email_news, name='send_email'),

    path("crypto_chart/", views.crypto_price_chart, name="crypto_chart"),
    
    path('coin-history/<int:coin_id>/', views.coin_history, name='coin_history'),
    path('crypto/<int:coin_id>/', views.crypto_detail, name='crypto_detail'),
    path('api/chart-data/', views.coin_history_api, name='coin_history_api'),
    path('api/backtest/', views.backtest_view, name='backtest_view'),

    path('membership/', views.membership_plans, name='membership_plans'), # 會員頁面
    path('upgrade_to_premium/', views.upgrade_to_premium, name='upgrade_to_premium'), #升級會員
    path('terms/', views.user_terms, name='user_terms'), # 使用者條款
    path('accounts/', include('allauth.urls')),#登入帳號(google驗證)
    

    
    path("delete_account/", views.delete_account, name="delete_account"),# 刪除帳號

    path('sign_in/', views.sign_in, name='sign_in'),
    path('user_profile/', views.user_profile, name='user_profile'),  # 个人资料页面


    path('', views.guanggao_shenfen_queren, name='home'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


