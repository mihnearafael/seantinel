from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('reports/', include('reports.urls')),
    path('', include('monitoring.urls')), # Dashboard-ul este pagina principală
]