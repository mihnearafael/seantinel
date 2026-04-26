from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.dashboard_map, name='dashboard'),
    path('scan/', views.trigger_mock_pipeline, name='trigger_pipeline'),
    path('proxy-map-image/', views.proxy_map_image, name='proxy_map_image'),
    path("vessels/", views.vessels_view),
    path("trails/", views.trails_view),
]