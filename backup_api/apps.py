# backup_api/apps.py
from django.apps import AppConfig
import os

class BackupApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backup_api'
    
    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
        
        try:
            from .scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            print(f"Scheduler could not start: {e}")