from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='weekly_report_list'),
    path('generate/', views.generate_weekly_report, name='generate_weekly_report'),
    path('report/<int:report_id>/', views.view_weekly_report_by_id, name='view_weekly_report_by_id'),
    path("classify/", views.classify_question, name="classify_question"),
    path('classify2/', views.classify_question2, name='classify_question2'),
]
