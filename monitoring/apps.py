import os
import threading
import asyncio
from django.apps import AppConfig

class MonitoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitoring"

    _started = False

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return

        if MonitoringConfig._started:
            return

        MonitoringConfig._started = True

        from .ais_monitoring import connect_ais_stream

        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(connect_ais_stream())

        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()

        print("AIS THREAD STARTED")