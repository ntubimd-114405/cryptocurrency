from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='ml_home'),
    path('add/', views.add_data_location, name='add_data_location'),
    path('<int:id>/', views.data_location_detail, name='data_location_detail'),
    path('data_location/<int:id>/run_program/', views.run_program, name='run_program'),
]

