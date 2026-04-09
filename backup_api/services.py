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
    
    # backup_api/services.py


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
            
            args = []
            if app_names:
                args.extend(app_names)
            
            exclude_args = ['--exclude', 'auth.permission', '--exclude', 'contenttypes']
            if exclude:
                for item in exclude:
                    exclude_args.extend(['--exclude', item])
            
            with f:
                call_command(
                    'dumpdata',
                    *args,
                    *exclude_args,
                    indent=2,
                    natural_foreign=True,
                    natural_primary=True,
                    stdout=f
                )
            
            result['database_backup'] = str(db_backup_file)
            
            if include_media and self.media_dir.exists():
                media_backup_file = temp_backup_dir / f"{backup_name}_media.tar.gz"
                
                with tarfile.open(media_backup_file, 'w:gz') as tar:
                    tar.add(self.media_dir, arcname='media')
                
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
                self.clean_database_completely()
                self.stdout_message("Database cleaned for replace mode")
            
            if str(db_backup_file).endswith('.gz'):
                temp_file = temp_restore_dir / "temp_restore.json"
                with gzip.open(db_backup_file, 'rt', encoding='utf-8') as f_in:
                    with open(temp_file, 'w', encoding='utf-8') as f_out:
                        f_out.write(f_in.read())
                call_command('loaddata', str(temp_file))
                temp_file.unlink()
            else:
                call_command('loaddata', str(db_backup_file))
            
            if include_media:
                media_files = list(temp_restore_dir.glob('*_media.tar.gz'))
                if media_files:
                    media_backup = media_files[0]
                    
                    if mode == 'replace' and self.media_dir.exists():
                        shutil.rmtree(self.media_dir)
                        self.media_dir.mkdir(parents=True, exist_ok=True)
                        self.stdout_message("Media folder cleaned for replace mode")
                    
                    with tarfile.open(media_backup, 'r:gz') as tar:
                        tar.extractall(settings.BASE_DIR)
                    
                    self.stdout_message("Media files restored")
            
            shutil.rmtree(temp_restore_dir)
            
            return {
                'success': True,
                'message': f"Successfully restored from {backup_filename} using mode='{mode}'",
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
        try:
            temp_restore_dir = Path(tempfile.mkdtemp())
            
            with tarfile.open(backup_stream, 'r:gz') as tar:
                tar.extractall(temp_restore_dir)
            
            db_files = list(temp_restore_dir.glob('*.json')) + list(temp_restore_dir.glob('*.json.gz'))
            if not db_files:
                return {
                    'success': False,
                    'error': 'No database backup found in archive'
                }
            
            db_backup_file = db_files[0]
            
            if mode == 'replace':
                self.clean_database_completely()
                self.stdout_message("Database cleaned for replace mode")
                
                if include_media and self.media_dir.exists():
                    shutil.rmtree(self.media_dir)
                    self.media_dir.mkdir(parents=True, exist_ok=True)
                    self.stdout_message("Media folder cleaned for replace mode")
            
            self.stdout_message("Restoring database from stream")
            
            if str(db_backup_file).endswith('.gz'):
                temp_file = temp_restore_dir / "temp_restore.json"
                with gzip.open(db_backup_file, 'rt', encoding='utf-8') as f_in:
                    with open(temp_file, 'w', encoding='utf-8') as f_out:
                        f_out.write(f_in.read())
                call_command('loaddata', str(temp_file))
                temp_file.unlink()
            else:
                call_command('loaddata', str(db_backup_file))
            
            self.stdout_message("Database restored successfully")
            
            if include_media:
                media_files = list(temp_restore_dir.glob('*_media.tar.gz'))
                if media_files:
                    media_backup = media_files[0]
                    
                    self.media_dir.mkdir(parents=True, exist_ok=True)
                    
                    with tarfile.open(media_backup, 'r:gz') as tar:
                        tar.extractall(settings.BASE_DIR)
                    
                    self.stdout_message("Media files restored successfully")
            
            shutil.rmtree(temp_restore_dir)
            
            return {
                'success': True,
                'message': f"Successfully restored from stream using mode='{mode}'",
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
    
    def clean_database_completely(self):
        from django.apps import apps
        
        all_models = apps.get_models()
        
        with connection.cursor() as cursor:
            db_engine = settings.DATABASES['default']['ENGINE']
            
            if 'postgresql' in db_engine:
                # PostgreSQL
                cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                    AND tablename NOT IN ('django_migrations', 'django_content_type', 'auth_permission')
                """)
                tables = cursor.fetchall()
                for table in tables:
                    try:
                        cursor.execute(f'TRUNCATE TABLE "{table[0]}" CASCADE;')
                        self.stdout_message(f"  Truncated: {table[0]}")
                    except Exception as e:
                        self.stdout_message(f"  Error truncating {table[0]}: {e}")
                        
            elif 'sqlite' in db_engine:
                cursor.execute("PRAGMA foreign_keys = OFF;")
                for model in all_models:
                    if not model._meta.managed:
                        continue
                    table_name = model._meta.db_table
                    if table_name not in ['django_migrations', 'django_content_type', 'auth_permission']:
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
                    if model._meta.db_table not in ['django_migrations', 'django_content_type', 'auth_permission']:
                        try:
                            model.objects.all().delete()
                            self.stdout_message(f"  Deleted from: {model._meta.db_table}")
                        except Exception as e:
                            self.stdout_message(f"  Error deleting from {model._meta.db_table}: {e}")
        
        self.stdout_message("Database cleaned completely")
    
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
        self.clean_database_completely()
    
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

# # backup_api/services.py
# import os
# import gzip
# from pathlib import Path
# import shutil
# from datetime import datetime
# import subprocess
# import tarfile
# import tempfile
# from django.conf import settings
# from django.db import connection

# class BackupService:
    
#     def __init__(self):
#         self.backup_dir = settings.BACKUP_CONFIG['BACKUP_DIR']
#         self.backup_dir.mkdir(parents=True, exist_ok=True)
#         self.media_dir = settings.MEDIA_ROOT
        
#         self.db_settings = settings.DATABASES['default']
#         self.db_name = self.db_settings['NAME']
#         self.db_user = self.db_settings['USER']
#         self.db_password = self.db_settings['PASSWORD']
#         self.db_host = self.db_settings.get('HOST', 'localhost')
#         self.db_port = self.db_settings.get('PORT', '5432')
    
#     def create_backup(self, app_names=None, compress=True, exclude=None, include_media=True):
        # """
        # إنشاء نسخة احتياطية باستخدام pg_dump (طريقة PostgreSQL الاحترافية)
        # """
        # # ✅ تنسيق الوقت لاسم الملف (بدون نقطتين)
        # timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
        # backup_name = f"backup_{timestamp_file}"
        
        # # ✅ تنسيق الوقت لـ API Response (ISO 8601 مع Z)
        # timestamp_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # temp_backup_dir = self.backup_dir / f"temp_{timestamp_file}"
        # temp_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # result = {
        #     'success': True,
        #     'created_at': timestamp_iso  # ✅ التنسيق الجديد
        # }
        
        # try:
        #     # ✅ 1. نسخ قاعدة البيانات باستخدام pg_dump
        #     db_backup_file = temp_backup_dir / f"{backup_name}.sql"
            
        #     # أمر pg_dump
        #     pg_dump_cmd = [
        #         'pg_dump',
        #         '-h', self.db_host,
        #         '-p', self.db_port,
        #         '-U', self.db_user,
        #         '-d', self.db_name,
        #         '-f', str(db_backup_file),
        #         '--format=plain',
        #         '--no-owner',
        #         '--no-privileges',
        #         '--verbose'
        #     ]
            
        #     env = os.environ.copy()
        #     env['PGPASSWORD'] = self.db_password
            
        #     self.stdout_message(f"📤 Creating database backup with pg_dump...")
        #     result_cmd = subprocess.run(
        #         pg_dump_cmd,
        #         env=env,
        #         capture_output=True,
        #         text=True
        #     )
            
        #     if result_cmd.returncode != 0:
        #         raise Exception(f"pg_dump failed: {result_cmd.stderr}")
            
        #     if db_backup_file.stat().st_size == 0:
        #         raise Exception("Database backup file is empty")
            
        #     self.stdout_message(f"✅ Database backup created: {db_backup_file} ({self.get_file_size(db_backup_file)})")
        #     result['database_backup'] = str(db_backup_file)
            
        #     # ✅ 2. ضغط ملف SQL إذا طلب ذلك
        #     if compress:
        #         gz_file = temp_backup_dir / f"{backup_name}.sql.gz"
        #         with open(db_backup_file, 'rb') as f_in:
        #             with gzip.open(gz_file, 'wb') as f_out:
        #                 shutil.copyfileobj(f_in, f_out)
        #         db_backup_file.unlink()  # حذف الملف غير المضغوط
        #         db_backup_file = gz_file
        #         self.stdout_message(f"✅ Database backup compressed: {gz_file}")
            
        #     # ✅ 3. نسخ ملفات media
        #     if include_media and self.media_dir.exists():
        #         media_backup_file = temp_backup_dir / f"{backup_name}_media.tar.gz"
                
        #         with tarfile.open(media_backup_file, 'w:gz') as tar:
        #             tar.add(self.media_dir, arcname='media')
                
        #         self.stdout_message(f"✅ Media backup created: {media_backup_file}")
        #         result['media_backup'] = str(media_backup_file)
            
        #     # ✅ 4. تجميع كل شيء في ملف واحد
        #     final_backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        #     with tarfile.open(final_backup_file, 'w:gz') as tar:
        #         for file in temp_backup_dir.iterdir():
        #             tar.add(file, arcname=file.name)
            
        #     self.stdout_message(f"✅ Final backup created: {final_backup_file}")
            
        #     # تنظيف المجلد المؤقت
        #     shutil.rmtree(temp_backup_dir)
            
        #     result['filename'] = final_backup_file.name
        #     result['size'] = self.get_file_size(final_backup_file)
            
        #     # تنظيف الملفات القديمة
        #     self.cleanup_old_backups()
            
        #     return result
            
        # except Exception as e:
        #     self.stdout_message(f"❌ Backup creation error: {e}")
        #     if temp_backup_dir.exists():
        #         shutil.rmtree(temp_backup_dir)
            
        #     return {
        #         'success': False,
        #         'error': str(e)
        #     }
    
#     def restore_backup(self, backup_filename, mode='restore', include_media=True):
#      
#         backup_file = self.backup_dir / backup_filename
        
#         if not backup_file.exists():
#             return {
#                 'success': False,
#                 'error': f"Backup file '{backup_filename}' not found"
#             }
        
#         temp_restore_dir = self.backup_dir / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#         temp_restore_dir.mkdir(parents=True, exist_ok=True)
        
#         try:
#             with tarfile.open(backup_file, 'r:gz') as tar:
#                 tar.extractall(temp_restore_dir)
            
#             sql_files = list(temp_restore_dir.glob('*.sql')) + list(temp_restore_dir.glob('*.sql.gz'))
#             if not sql_files:
#                 return {
#                     'success': False,
#                     'error': 'No database backup found in archive'
#                 }
            
#             db_backup_file = sql_files[0]
            
#             if mode == 'replace':
#                 self.clean_database_completely()
#                 self.stdout_message("Database cleaned for replace mode")
                
#                 if include_media and self.media_dir.exists():
#                     shutil.rmtree(self.media_dir)
#                     self.media_dir.mkdir(parents=True, exist_ok=True)
#                     self.stdout_message("Media folder cleaned for replace mode")
            
#             self.stdout_message(f"Restoring database from: {db_backup_file}")
            
#             if str(db_backup_file).endswith('.gz'):
#                 sql_file = temp_restore_dir / "temp_restore.sql"
#                 with gzip.open(db_backup_file, 'rb') as f_in:
#                     with open(sql_file, 'wb') as f_out:
#                         shutil.copyfileobj(f_in, f_out)
#                 db_backup_file = sql_file
            
#             psql_cmd = [
#                 'psql',
#                 '-h', self.db_host,
#                 '-p', self.db_port,
#                 '-U', self.db_user,
#                 '-d', self.db_name,
#                 '-f', str(db_backup_file),
#                 '--quiet'
#             ]
            
#             env = os.environ.copy()
#             env['PGPASSWORD'] = self.db_password
            
#             result_cmd = subprocess.run(
#                 psql_cmd,
#                 env=env,
#                 capture_output=True,
#                 text=True
#             )
            
#             if result_cmd.returncode != 0:
#                 raise Exception(f"psql restore failed: {result_cmd.stderr}")
            
#             self.stdout_message("Database restored successfully")
            
#             if include_media:
#                 media_files = list(temp_restore_dir.glob('*_media.tar.gz'))
#                 if media_files:
#                     media_backup = media_files[0]
                    
#                     self.media_dir.mkdir(parents=True, exist_ok=True)
                    
#                     with tarfile.open(media_backup, 'r:gz') as tar:
#                         tar.extractall(settings.BASE_DIR)
                    
#                     self.stdout_message("Media files restored successfully")
            
#             shutil.rmtree(temp_restore_dir)
            
#             return {
#                 'success': True,
#                 'message': f"Successfully restored from {backup_filename} using mode='{mode}'",
#                 'mode': mode
#             }
            
#         except Exception as e:
#             self.stdout_message(f"Restore error: {e}")
#             if temp_restore_dir.exists():
#                 shutil.rmtree(temp_restore_dir)
            
#             return {
#                 'success': False,
#                 'error': str(e)
#             }
    
#     def restore_from_stream(self, backup_stream, mode='restore', include_media=True):
#      
#         try:
#             temp_restore_dir = Path(tempfile.mkdtemp())
            
#             with tarfile.open(backup_stream, 'r:gz') as tar:
#                 tar.extractall(temp_restore_dir)
            
#             sql_files = list(temp_restore_dir.glob('*.sql')) + list(temp_restore_dir.glob('*.sql.gz'))
#             if not sql_files:
#                 return {
#                     'success': False,
#                     'error': 'No database backup found in archive'
#                 }
            
#             db_backup_file = sql_files[0]
            
#             if mode == 'replace':
#                 self.clean_database_completely()
#                 self.stdout_message("Database cleaned for replace mode")
                
#                 if include_media and self.media_dir.exists():
#                     shutil.rmtree(self.media_dir)
#                     self.media_dir.mkdir(parents=True, exist_ok=True)
#                     self.stdout_message("Media folder cleaned for replace mode")
            
#             self.stdout_message("Restoring database from stream")
            
#             if str(db_backup_file).endswith('.gz'):
#                 sql_file = temp_restore_dir / "temp_restore.sql"
#                 with gzip.open(db_backup_file, 'rb') as f_in:
#                     with open(sql_file, 'wb') as f_out:
#                         shutil.copyfileobj(f_in, f_out)
#                 db_backup_file = sql_file
            
#             psql_cmd = [
#                 'psql',
#                 '-h', self.db_host,
#                 '-p', self.db_port,
#                 '-U', self.db_user,
#                 '-d', self.db_name,
#                 '-f', str(db_backup_file),
#                 '--quiet'
#             ]
            
#             env = os.environ.copy()
#             env['PGPASSWORD'] = self.db_password
            
#             result_cmd = subprocess.run(
#                 psql_cmd,
#                 env=env,
#                 capture_output=True,
#                 text=True
#             )
            
#             if result_cmd.returncode != 0:
#                 raise Exception(f"psql restore failed: {result_cmd.stderr}")
            
#             self.stdout_message("Database restored successfully")
            
#             if include_media:
#                 media_files = list(temp_restore_dir.glob('*_media.tar.gz'))
#                 if media_files:
#                     media_backup = media_files[0]
#                     self.media_dir.mkdir(parents=True, exist_ok=True)
#                     with tarfile.open(media_backup, 'r:gz') as tar:
#                         tar.extractall(settings.BASE_DIR)
#                     self.stdout_message("Media files restored successfully")
            
#             shutil.rmtree(temp_restore_dir)
            
#             return {
#                 'success': True,
#                 'message': f"Successfully restored from stream using mode='{mode}'",
#                 'mode': mode
#             }
            
#         except Exception as e:
#             self.stdout_message(f"Restore error: {e}")
#             return {
#                 'success': False,
#                 'error': str(e)
#             }
    
#     def clean_database_completely(self):
#         with connection.cursor() as cursor:
#             cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
            
#             cursor.execute("""
#                 SELECT tablename FROM pg_tables 
#                 WHERE schemaname = 'public'
#                 AND tablename NOT IN ('django_migrations', 'django_content_type', 'auth_permission', 'spatial_ref_sys')
#             """)
            
#             tables = cursor.fetchall()
#             for table in tables:
#                 try:
#                     cursor.execute(f'TRUNCATE TABLE "{table[0]}" CASCADE;')
#                     self.stdout_message(f"  Truncated: {table[0]}")
#                 except Exception as e:
#                     self.stdout_message(f"  Error truncating {table[0]}: {e}")
            
#             cursor.execute("""
#                 SELECT sequence_name FROM information_schema.sequences 
#                 WHERE sequence_schema = 'public'
#             """)
#             sequences = cursor.fetchall()
#             for seq in sequences:
#                 try:
#                     cursor.execute(f'ALTER SEQUENCE "{seq[0]}" RESTART WITH 1;')
#                 except:
#                     pass
        
#         self.stdout_message("Database cleaned completely")
    
#     def list_backups(self):
    # """قائمة بجميع النسخ الاحتياطية"""
    #     backups = []
        
    #     for file in sorted(self.backup_dir.glob('backup_*.tar.gz'), reverse=True):
    #         stat = file.stat()
            
    #         # ✅ تحويل الوقت إلى صيغة ISO مع Z
    #         created_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace('+00:00', 'Z')
            
    #         backup_type = self.get_backup_type(file)
            
    #         backups.append({
    #             'filename': file.name,
    #             'size': self.get_file_size(file),
    #             'created_at': created_at,  # ✅ نفس التنسيق
    #             'file_path': str(file),
    #             'type': backup_type
    #         })
        
    #     return backups
    
#     def get_backup_type(self, backup_file):
#         try:
#             with tarfile.open(backup_file, 'r:gz') as tar:
#                 members = tar.getmembers()
#                 has_db = any(m.name.endswith('.sql') or m.name.endswith('.sql.gz') for m in members)
#                 has_media = any('media' in m.name for m in members)
                
#                 if has_db and has_media:
#                     return 'Full (Database + Media)'
#                 elif has_db:
#                     return 'Database Only'
#                 elif has_media:
#                     return 'Media Only'
#                 return 'Unknown'
#         except:
#             return 'Unknown'
    
#     def get_file_size(self, file_path):
#         size_bytes = file_path.stat().st_size
#         for unit in ['B', 'KB', 'MB', 'GB']:
#             if size_bytes < 1024.0:
#                 return f"{size_bytes:.2f} {unit}"
#             size_bytes /= 1024.0
#         return f"{size_bytes:.2f} TB"
    
#     def cleanup_old_backups(self):
#         backups = sorted(self.backup_dir.glob('backup_*.tar.gz'), key=lambda x: x.stat().st_mtime, reverse=True)
#         max_files = settings.BACKUP_CONFIG.get('MAX_BACKUP_FILES', 5)
        
#         for old_backup in backups[max_files:]:
#             old_backup.unlink()
#             self.stdout_message(f"Deleted old backup: {old_backup.name}")
    
#     def delete_backup(self, backup_filename):
#         backup_file = self.backup_dir / backup_filename
#         if not backup_file.exists():
#             return {'success': False, 'error': f"Backup file '{backup_filename}' not found"}
        
#         backup_file.unlink()
#         return {'success': True, 'message': f"Backup '{backup_filename}' deleted successfully"}
    
#     def stdout_message(self, message):
#         print(f"[BackupService] {message}")