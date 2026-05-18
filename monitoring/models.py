from django.db import models

class AISHistory(models.Model):
    mmsi = models.BigIntegerField(db_index=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    course = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"AIS {self.mmsi} at {self.timestamp}"
