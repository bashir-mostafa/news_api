# backup_api/management/commands/backup_status.py
from django.core.management.base import BaseCommand
from django.conf import settings
from backup_api.services import BackupService
from datetime import datetime

class Command(BaseCommand):
    help = 'Show backup status and statistics'
    
    def handle(self, *args, **options):
        service = BackupService()
        backups = service.list_backups()
        
        self.stdout.write(self.style.SUCCESS('\n=== Backup Status ==='))
        self.stdout.write(f'Auto backup enabled: {settings.BACKUP_CONFIG.get("AUTO_BACKUP_ENABLED", True)}')
        self.stdout.write(f'Backup directory: {settings.BACKUP_CONFIG["BACKUP_DIR"]}')
        self.stdout.write(f'Max backup files: {settings.BACKUP_CONFIG.get("MAX_BACKUP_FILES", 1)}')
        self.stdout.write(f'Keep days: {settings.BACKUP_CONFIG.get("AUTO_BACKUP_KEEP_DAYS", 1)}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal backups: {len(backups)}'))
        
        if backups:
            self.stdout.write('\nLast 1 backups:')
            for backup in backups[:1]:
                self.stdout.write(f'   - {backup["filename"]} ({backup["size"]}) - {backup["created_at"]}')