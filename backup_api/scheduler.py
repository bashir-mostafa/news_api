# backup_api/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management import call_command
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
scheduler = None

def start_scheduler():
    global scheduler
    
    if not settings.BACKUP_CONFIG.get('AUTO_BACKUP_ENABLED', True):
        logger.info("Auto backup is disabled in settings")
        return None
    
    scheduler = BackgroundScheduler()
    
    hour = settings.BACKUP_CONFIG.get('AUTO_BACKUP_HOUR', 0)
    minute = settings.BACKUP_CONFIG.get('AUTO_BACKUP_MINUTE', 0)
    
    scheduler.add_job(
        create_daily_backup,
        trigger=CronTrigger(hour=hour, minute=minute),
        id='daily_backup',
        name='Daily Backup Job',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Backup scheduler started (daily at {hour:02d}:{minute:02d})")
    
    return scheduler

def stop_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("Backup scheduler stopped")

def create_daily_backup():
    try:
        call_command('daily_backup')
        logger.info("Daily backup completed successfully")
    except Exception as e:
        logger.error(f"Daily backup failed: {str(e)}")