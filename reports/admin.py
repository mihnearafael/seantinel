from django.contrib import admin
from .models import ProtectedArea, IllegalReport

admin.site.register(ProtectedArea)
admin.site.register(IllegalReport)