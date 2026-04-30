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
        self._seed_content_types()

    def _seed_content_types(self):
        from django.db.utils import OperationalError, ProgrammingError
        
        try:
            from .models import ContentType
            
            content_types = [
                ('إنفوجرافيك', 'Infographic', 'Înfografîk', 1),
('فيديو', 'Video', 'Vîdyo', 2),
('وثائقي', 'Documentary', 'Belgesel', 3),
('تقرير', 'Report', 'Rapor', 4),
('استبيان', 'Survey', 'Anket', 5),
('حدث', 'Event', 'Bûyer', 6),
('مجلة', 'Magazine', 'Kovar', 7),
('كتاب', 'Book', 'Pirtûk', 8),
('دراسات', 'Studies', 'Lêkolîn', 9),
('تحليلات', 'Analytics', 'Analîz', 10),
('مقال رأي', 'Opinion Article', 'Gotara RAY', 11),
('ملفات', 'Files', 'Pel', 12),
            ]
            
            for name_ar, name_en, name_ku, priority in content_types:
                ContentType.objects.get_or_create(
                    name_ar=name_ar,
                    defaults={
                        'name_en': name_en,
                        'name_ku': name_ku,
                        'priority': priority
                    }
                )
        except (OperationalError, ProgrammingError):
            pass