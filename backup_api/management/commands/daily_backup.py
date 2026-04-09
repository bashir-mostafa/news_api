# backup_api/management/commands/daily_backup.py
from django.core.management.base import BaseCommand
from django.conf import settings
from backup_api.services import BackupService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create daily automatic backup'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--compress',
            action='store_true',
            default=True,
            help='Compress the backup (default: True)',
        )
        parser.add_argument(
            '--no-compress',
            action='store_false',
            dest='compress',
            help='Do not compress the backup',
        )
        parser.add_argument(
            '--include-media',
            action='store_true',
            default=True,
            help='Include media files (default: True)',
        )
        parser.add_argument(
            '--no-media',
            action='store_false',
            dest='include_media',
            help='Exclude media files',
        )
    
    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Starting daily backup...'))
            
            service = BackupService()
            
            result = service.create_backup(
                app_names=['accounts', 'content'],
                compress=options['compress'],
                include_media=options['include_media']
            )
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(
                    f'Daily backup created successfully: {result["filename"]}'
                ))
                self.stdout.write(self.style.SUCCESS(
                    f'   Size: {result["size"]} bytes'
                ))
                self.stdout.write(self.style.SUCCESS(
                    f'   Created at: {result["created_at"]}'
                ))
                
                self.cleanup_old_backups(keep_last=1)
                
            else:
                self.stdout.write(self.style.ERROR(
                    f' Daily backup failed: {result["error"]}'
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            logger.error(f'Daily backup error: {str(e)}')
    
    def cleanup_old_backups(self, keep_last=1):
        try:
            service = BackupService()
            backups = service.list_backups()
            
            if len(backups) > keep_last:
                old_backups = backups[keep_last:]
                for backup in old_backups:
                    service.delete_backup(backup['filename'])
                    self.stdout.write(self.style.WARNING(
                        f'Deleted old backup: {backup["filename"]}'
                    ))
                    
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'   Cleanup failed: {str(e)}'
            ))