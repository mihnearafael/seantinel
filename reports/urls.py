from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('<int:pk>/', views.report_detail, name='report_detail'),
    path('generate/', views.generate_report, name='generate_report'),
    path('<int:pk>/pdf/', views.download_report_pdf, name='download_pdf'),
]