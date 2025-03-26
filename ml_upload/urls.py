from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='ml_home'),
    path("status/", views.notebook_status, name="notebook_status"),
]

