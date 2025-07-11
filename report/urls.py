from django.urls import path
from .views import view_weekly_report_by_id,report_list,generate_weekly_report

urlpatterns = [
    path('', report_list, name='weekly_report_list'),
    path('generate/', generate_weekly_report, name='generate_weekly_report'),
    path('report/<int:report_id>/', view_weekly_report_by_id, name='view_weekly_report_by_id'),
]