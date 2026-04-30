# content/apps.py
from django.apps import AppConfig
import os

class ContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content'
    
    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
        
        try:
            from .scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            print(f"Posts scheduler could not start: {e}")

