from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='weekly_report_list'),
    path('generate/', views.generate_weekly_report, name='generate_weekly_report'),
    path('<int:report_id>/', views.view_weekly_report_by_id, name='view_weekly_report_by_id'),
    path("chat/", views.chat_view, name="chat"),
    path("api/classify/", views.classify_question_api, name="classify_question_api"),
]
