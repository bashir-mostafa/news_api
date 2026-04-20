from django.apps import AppConfig
import os

class BackupApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backup_api'
    _scheduler_started = False  

    def ready(self):
        import sys

        if 'runserver' not in sys.argv:
            return

        if BackupApiConfig._scheduler_started:
            return
        BackupApiConfig._scheduler_started = True

        import atexit
        try:
            from .scheduler import start_scheduler, stop_scheduler
            start_scheduler()
            atexit.register(stop_scheduler)
            print("✅ Backup scheduler initialized")  
        except Exception as e:
            print(f"❌ Scheduler could not start: {e}")