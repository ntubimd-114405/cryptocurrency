# agent/urls.py
from django.urls import path
from . import views


app_name = 'agent'

urlpatterns = [
    path('', views.questionnaire_list, name='questionnaire_list'),
    path('questionnaire/<int:questionnaire_id>/', views.questionnaire_detail, name='questionnaire_detail'),
    path('questionnaire/<int:questionnaire_id>/reset/', views.reset_questionnaire_answers, name='reset_questionnaire_answers'),
    path('analyze/all/', views.analysis_result_view, name='analysis_result_view'),
    path("chat/", views.chat_page, name="chat_page"),
    path("ask/", views.knowledge_chat_view, name="knowledge_chat"),
    path("invest/", views.invest_view, name="invest_view"),
    path("ema_detail/", views.ema_detail, name="ema_detail"),
    path("rsi_detail/", views.rsi_detail, name="rsi_detail"),
    path("macd_detail/", views.macd_detail, name="macd_detail"),
]

