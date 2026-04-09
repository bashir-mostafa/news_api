# content/scheduler.py
import threading
import time
from django.core.management import call_command
from django.conf import settings

scheduler_thread = None

def start_scheduler():
    global scheduler_thread
    
    stop_scheduler()
    
    scheduler_thread = threading.Thread(target=run_publish_scheduler, daemon=True)
    scheduler_thread.start()
    print("Posts publish scheduler started (checks every 5 minute)")
    
    return scheduler_thread

def stop_scheduler():
    global scheduler_thread
    scheduler_thread = None

def run_publish_scheduler():
    while True:
        try:
            call_command('publish_scheduled_posts')
            
            time.sleep(300) 
            
        except Exception as e:
            print(f" Posts publish scheduler error: {e}")
            time.sleep(300)