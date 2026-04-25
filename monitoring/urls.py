from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.dashboard_map, name='dashboard'),
    path('scan/', views.trigger_mock_pipeline, name='trigger_pipeline'),
]