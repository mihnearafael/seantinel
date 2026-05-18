from django.contrib import admin
from .models import AISHistory

@admin.register(AISHistory)
class AISHistoryAdmin(admin.ModelAdmin):
    list_display = ('mmsi', 'latitude', 'longitude', 'speed', 'course', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('mmsi',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    readonly_fields = ('mmsi', 'latitude', 'longitude', 'course', 'speed', 'timestamp')
    
    def has_add_permission(self, request):
        # We don't want to manually add AIS history entries via admin
        return False
