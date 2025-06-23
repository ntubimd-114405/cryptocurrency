# agent/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('questionnaire/', views.user_questionnaire, name='user_questionnaire'),
    path('portfolio/', views.asset_suggestion, name='asset_suggestion'),
]
