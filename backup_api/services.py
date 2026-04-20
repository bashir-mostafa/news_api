# backup_api/services.py
import os
import json
import gzip
from pathlib import Path
import shutil
from datetime import datetime
import subprocess
import tarfile
import tempfile
from django.conf import settings
from django.core.management import call_command
from django.core.management.commands import dumpdata, loaddata
from django.db import connection
from io import StringIO
from datetime import datetime, timezone

class BackupService:
    
    def __init__(self):
        self.backup_dir = settings.BACKUP_CONFIG['BACKUP_DIR']
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir = settings.MEDIA_ROOT
        
        self.db_settings = settings.DATABASES['default']
        self.db_name = self.db_settings['NAME']
        self.db_user = self.db_settings['USER']
        self.db_password = self.db_settings.get('PASSWORD', '')
        self.db_host = self.db_settings.get('HOST', 'localhost')
        self.db_port = self.db_settings.get('PORT', '5432')
    
    def create_backup(self, app_names=None, compress=True, exclude=None, include_media=True):
        timestamp_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp_file}"
        
        temp_backup_dir = self.backup_dir / f"temp_{timestamp_file}"
        temp_backup_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            'success': True,
            'database_backup': None,
            'media_backup': None,
            'created_at': timestamp_iso  
        }
        
        try:
            if compress:
                db_backup_file = temp_backup_dir / f"{backup_name}.json.gz"
                f = gzip.open(db_backup_file, 'wt', encoding='utf-8')
            else:
                db_backup_file = temp_backup_dir / f"{backup_name}.json"
                f = open(db_backup_file, 'w', encoding='utf-8')
            
            from django.apps import apps
            
            if app_names:
                backup_apps = app_names
            else:
                excluded_apps = ['accounts', 'django', 'rest_framework.authtoken', 'token_blacklist']
                backup_apps = []
                
                for app_config in apps.get_app_configs():
                    app_name = app_config.name
                    skip = False
                    for excluded in excluded_apps:
                        if app_name == excluded or app_name.startswith('django.'):
                            skip = True
                            break
                    if not skip and app_config.models: 
                        backup_apps.append(app_name)
            
            print(f"[BackupService] Creating backup for apps: {backup_apps}")
            
            with f:
                if backup_apps:
                    call_command(
                        'dumpdata',
                        *backup_apps,
                        indent=2,
                        natural_foreign=True,
                        natural_primary=True,
                        stdout=f
                    )
                else:
                    return {
                        'success': False,
                        'error': 'No applications found to backup'
                    }
            
            result['database_backup'] = str(db_backup_file)
            
            if include_media and self.media_dir.exists():
                media_backup_file = temp_backup_dir / f"{backup_name}_media.tar.gz"
                
                with tarfile.open(media_backup_file, 'w:gz') as tar:
                    for item in self.media_dir.iterdir():
                        if item.name != 'accounts':  
                            tar.add(item, arcname=f'media/{item.name}')
                            print(f"[BackupService] Added to media backup: {item.name}")
                        else:
                            print(f"[BackupService] Skipped accounts media folder")
                
                result['media_backup'] = str(media_backup_file)
            
            final_backup_file = self.backup_dir / f"{backup_name}.tar.gz"
            with tarfile.open(final_backup_file, 'w:gz') as tar:
                tar.add(temp_backup_dir, arcname='')
            
            shutil.rmtree(temp_backup_dir)
            
            result['filename'] = final_backup_file.name
            result['size'] = self.get_file_size(final_backup_file)
            
            self.cleanup_old_backups()
            
            return result
            
        except Exception as e:
            if temp_backup_dir.exists():
                shutil.rmtree(temp_backup_dir)
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def restore_backup(self, backup_filename, mode='restore', include_media=True):
        backup_file = self.backup_dir / backup_filename
        
        if not backup_file.exists():
            return {
                'success': False,
                'error': f"Backup file '{backup_filename}' not found"
            }
        
        temp_restore_dir = self.backup_dir / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_restore_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(temp_restore_dir)
            
            db_files = list(temp_restore_dir.glob('*.json')) + list(temp_restore_dir.glob('*.json.gz'))
            if not db_files:
                return {
                    'success': False,
                    'error': 'No database backup found in archive'
                }
            
            db_backup_file = db_files[0]
            
            if mode == 'replace':
                self.clean_database_completely(preserve_accounts=True)
                self.stdout_message("Database cleaned for replace mode (accounts preserved)")
            
            if str(db_backup_file).endswith('.gz'):
                temp_file = temp_restore_dir / "temp_restore.json"
                with gzip.open(db_backup_file, 'rt', encoding='utf-8') as f_in:
                    data = json.load(f_in)
                
                if isinstance(data, list):
                    filtered_data = [item for item in data if not item.get('model', '').startswith('accounts.')]
                else:
                    filtered_data = data
                
                with open(temp_file, 'w', encoding='utf-8') as f_out:
                    json.dump(filtered_data, f_out, indent=2)
                call_command('loaddata', str(temp_file))
                temp_file.unlink()
            else:
                with open(db_backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    filtered_data = [item for item in data if not item.get('model', '').startswith('accounts.')]
                else:
                    filtered_data = data
                
                temp_file = temp_restore_dir / "temp_restore_filtered.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(filtered_data, f, indent=2)
                call_command('loaddata', str(temp_file))
                temp_file.unlink()
            
            if include_media:
                media_files = list(temp_restore_dir.glob('*_media.tar.gz'))
                if media_files:
                    media_backup = media_files[0]
                    
                    if mode == 'replace' and self.media_dir.exists():
                        accounts_media_path = self.media_dir / 'accounts'
                        accounts_backup = None
                        if accounts_media_path.exists():
                            accounts_backup = Path(tempfile.mkdtemp()) / 'accounts'
                            shutil.copytree(accounts_media_path, accounts_backup)
                            self.stdout_message("Accounts media folder preserved")
                        
                        shutil.rmtree(self.media_dir)
                        self.media_dir.mkdir(parents=True, exist_ok=True)
                        
                        if accounts_backup and accounts_backup.exists():
                            shutil.copytree(accounts_backup, accounts_media_path)
                            self.stdout_message("Accounts media folder restored")
                    
                    with tarfile.open(media_backup, 'r:gz') as tar:
                        tar.extractall(settings.BASE_DIR)
                    
                    self.stdout_message("Media files restored")
            
            shutil.rmtree(temp_restore_dir)
            
            return {
                'success': True,
                'message': f"Successfully restored from {backup_filename} using mode='{mode}' (accounts preserved)",
                'mode': mode
            }
            
        except Exception as e:
            if temp_restore_dir.exists():
                shutil.rmtree(temp_restore_dir)
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def restore_from_stream(self, backup_stream, mode='restore', include_media=True):
        temp_restore_dir = None
        try:
            temp_restore_dir = Path(tempfile.mkdtemp())
            
            if hasattr(backup_stream, 'seek'):
                backup_stream.seek(0)
            
            with tarfile.open(fileobj=backup_stream, mode='r:gz') as tar:
                tar.extractall(temp_restore_dir)
            
            db_files = list(temp_restore_dir.glob('*.json')) + list(temp_restore_dir.glob('*.json.gz'))
            if not db_files:
                return {
                    'success': False,
                    'error': 'No database backup found in archive'
                }
            
            db_backup_file = db_files[0]
            
            if mode == 'replace':
                self.clean_database_completely(preserve_accounts=True)
                self.stdout_message("Database cleaned for replace mode (accounts preserved)")
                
                if include_media and self.media_dir.exists():
                    accounts_media_path = self.media_dir / 'accounts'
                    accounts_backup = None
                    if accounts_media_path.exists():
                        accounts_backup = Path(tempfile.mkdtemp()) / 'accounts'
                        shutil.copytree(accounts_media_path, accounts_backup)
                        self.stdout_message("Accounts media folder preserved")
                    
                    shutil.rmtree(self.media_dir)
                    self.media_dir.mkdir(parents=True, exist_ok=True)
                    
                    if accounts_backup and accounts_backup.exists():
                        shutil.copytree(accounts_backup, accounts_media_path)
                        self.stdout_message("Accounts media folder restored")
            
            self.stdout_message("Restoring database from stream")
            
            if str(db_backup_file).endswith('.gz'):
                temp_file = temp_restore_dir / "temp_restore.json"
                with gzip.open(db_backup_file, 'rt', encoding='utf-8') as f_in:
                    data = json.load(f_in)
                
                if isinstance(data, list):
                    filtered_data = [item for item in data if not item.get('model', '').startswith('accounts.')]
                else:
                    filtered_data = data
                
                with open(temp_file, 'w', encoding='utf-8') as f_out:
                    json.dump(filtered_data, f_out, indent=2)
                call_command('loaddata', str(temp_file))
                temp_file.unlink()
            else:
                with open(db_backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    filtered_data = [item for item in data if not item.get('model', '').startswith('accounts.')]
                else:
                    filtered_data = data
                
                temp_file = temp_restore_dir / "temp_restore_filtered.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(filtered_data, f, indent=2)
                call_command('loaddata', str(temp_file))
                temp_file.unlink()
            
            self.stdout_message("Database restored successfully (accounts excluded)")
            
            if include_media:
                media_files = list(temp_restore_dir.glob('*_media.tar.gz'))
                if media_files:
                    media_backup = media_files[0]
                    self.media_dir.mkdir(parents=True, exist_ok=True)
                    
                    with tarfile.open(media_backup, 'r:gz') as tar:
                        tar.extractall(settings.BASE_DIR)
                    
                    self.stdout_message("Media files restored successfully")
            
            return {
                'success': True,
                'message': f"Successfully restored from stream using mode='{mode}' (accounts preserved)",
                'mode': mode
            }
            
        except Exception as e:
            self.stdout_message(f"Restore error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            if temp_restore_dir and temp_restore_dir.exists():
                shutil.rmtree(temp_restore_dir, ignore_errors=True)
    
    def clean_database_completely(self, preserve_accounts=True):
   
        from django.apps import apps
        
        all_models = apps.get_models()
        
        with connection.cursor() as cursor:
            db_engine = settings.DATABASES['default']['ENGINE']
            
            if 'postgresql' in db_engine:
                cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                    AND tablename NOT IN ('django_migrations', 'django_content_type', 'auth_permission')
                """)
                tables = cursor.fetchall()
                for table in tables:
                    table_name = table[0]
                    if preserve_accounts and table_name.startswith('accounts_'):
                        self.stdout_message(f"  Skipped (preserved): {table_name}")
                        continue
                    try:
                        cursor.execute(f'TRUNCATE TABLE "{table_name}" CASCADE;')
                        self.stdout_message(f"  Truncated: {table_name}")
                    except Exception as e:
                        self.stdout_message(f"  Error truncating {table_name}: {e}")
                        
            elif 'sqlite' in db_engine:
                cursor.execute("PRAGMA foreign_keys = OFF;")
                for model in all_models:
                    if not model._meta.managed:
                        continue
                    table_name = model._meta.db_table
                    if table_name in ['django_migrations', 'django_content_type', 'auth_permission']:
                        continue
                    if preserve_accounts and table_name.startswith('accounts_'):
                        self.stdout_message(f"  Skipped (preserved): {table_name}")
                        continue
                    try:
                        cursor.execute(f"DELETE FROM {table_name};")
                        self.stdout_message(f"  Deleted from: {table_name}")
                    except Exception as e:
                        self.stdout_message(f"  Error deleting from {table_name}: {e}")
                cursor.execute("PRAGMA foreign_keys = ON;")
                
            else:
                for model in all_models:
                    if not model._meta.managed:
                        continue
                    table_name = model._meta.db_table
                    if table_name in ['django_migrations', 'django_content_type', 'auth_permission']:
                        continue
                    if preserve_accounts and table_name.startswith('accounts_'):
                        self.stdout_message(f"  Skipped (preserved): {table_name}")
                        continue
                    try:
                        model.objects.all().delete()
                        self.stdout_message(f"  Deleted from: {model._meta.db_table}")
                    except Exception as e:
                        self.stdout_message(f"  Error deleting from {model._meta.db_table}: {e}")
        
        self.stdout_message("Database cleaned completely (accounts preserved)")
    
    def delete_backup(self, backup_filename):
        backup_file = self.backup_dir / backup_filename
        
        if not backup_file.exists():
            return {
                'success': False,
                'error': f"Backup file '{backup_filename}' not found"
            }
        
        try:
            backup_file.unlink()
            self.stdout_message(f"Deleted backup: {backup_filename}")
            return {
                'success': True,
                'message': f"Backup '{backup_filename}' deleted successfully"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def clean_database(self):
        self.clean_database_completely(preserve_accounts=True)
    
    def list_backups(self):
        backups = []
        
        for file in sorted(self.backup_dir.glob('backup_*.tar.gz'), reverse=True):
            stat = file.stat()
            
            created_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace('+00:00', 'Z')
            
            backup_type = self.get_backup_type(file)
            
            backups.append({
                'filename': file.name,
                'size': self.get_file_size(file),
                'created_at': created_at,  
                'file_path': str(file),
                'type': backup_type
            })
        
        return backups
    
    def get_backup_type(self, backup_file):
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                members = tar.getmembers()
                has_db = any(m.name.endswith('.json') for m in members)
                has_media = any('media' in m.name for m in members)
                
                if has_db and has_media:
                    return 'Full (Database + Media)'
                elif has_db:
                    return 'Database Only'
                elif has_media:
                    return 'Media Only'
                else:
                    return 'Unknown'
        except:
            return 'Unknown'
    
    def get_file_size(self, file_path):
        size_bytes = file_path.stat().st_size
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.2f} TB"
    
    def cleanup_old_backups(self):
        backups = sorted(self.backup_dir.glob('backup_*.tar.gz'), key=lambda x: x.stat().st_mtime, reverse=True)
        max_files = settings.BACKUP_CONFIG.get('MAX_BACKUP_FILES', 5)
        
        for old_backup in backups[max_files:]:
            old_backup.unlink()
            self.stdout_message(f"Deleted old backup: {old_backup.name}")
    
    def stdout_message(self, message):
        print(f"[BackupService] {message}")
