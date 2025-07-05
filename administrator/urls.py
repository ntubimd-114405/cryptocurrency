# administrator/urls.py
from django.urls import path , include
from .views import *

app_name = 'administrator'  # 添加這行，設定 namespace

urlpatterns = [
    path('', dashboard, name='administrator_dashboard'),

    path('user-management/', user_management, name='user_management'),
    path('user-management/edit/<int:user_id>/', edit_user, name='edit_user'),

    path('crypto-management/', crypto_management, name='crypto_management'),
    path('edit-crypto-management/<int:id>/', edit_crypto, name='edit_crypto'),
    path('delete-crypto-management/<int:id>/', delete_crypto, name='delete_crypto'),
    
    path("api/", include("chatbot.urls")),
]
