# agent/urls.py
from django.urls import path
from . import views

app_name = 'agent'

urlpatterns = [
    path('', views.questionnaire_list, name='questionnaire_list'),
    path('questionnaire/<int:questionnaire_id>/', views.questionnaire_detail, name='questionnaire_detail'),
]
