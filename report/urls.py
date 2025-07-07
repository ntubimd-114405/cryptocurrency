from django.urls import path
from .views import weekly_report_view,full_month_data_view

urlpatterns = [
    path('weekly-report/', weekly_report_view, name='weekly_report'),
    path('monthly-data/', full_month_data_view, name='monthly_data_view'),
]