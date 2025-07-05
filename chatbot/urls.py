from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_page, name='chatbot_page'),
    path('api/chat/', views.chat_api, name='chat_api'),
]
