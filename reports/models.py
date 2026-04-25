from django.db import models
from django.conf import settings


class ProtectedArea(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    protected_species = models.TextField(help_text="Ex: Sturion, Delfin, Păsări rare")

    geometry_json = models.JSONField(help_text="GeoJSON polygon data")

    def __str__(self):
        return self.name


class IllegalReport(models.Model):
    STATUS_CHOICES = [
        ('UNCONFIRMED', 'AI Detected / Unconfirmed'),
        ('INVESTIGATING', 'Under Investigation'),
        ('CONFIRMED', 'Confirmed Illegal Fishing'),
        ('FALSE_ALARM', 'False Alarm'),
    ]

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    latitude = models.FloatField()
    longitude = models.FloatField()

    ship_name = models.CharField(max_length=100, default="UNKNOWN VESSEL")
    mmsi = models.CharField(max_length=20, blank=True, null=True)
    flag = models.CharField(max_length=50, blank=True, null=True)

    confidence_score = models.IntegerField(default=0, help_text="AI Confidence Score %")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNCONFIRMED')
    area = models.ForeignKey(ProtectedArea, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"[{self.status}] Threat at {self.latitude}, {self.longitude}"