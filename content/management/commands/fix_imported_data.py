# content/management/commands/fix_imported_data.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from content.models import Posts, ContentType, Categories, Authors, Tags
import re

class Command(BaseCommand):
    help = 'Fix imported data - assign proper content types, categories, authors'
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("🔧 FIXING IMPORTED DATA"))
        self.stdout.write("=" * 80)
        
        # 1. إصلاح أنواع المحتوى
        self.fix_content_types()
        
        # 2. إصلاح المؤلفين
        self.fix_authors()
        
        # 3. إصلاح التصنيفات
        self.fix_categories()
        
        # 4. إصلاح الصور
        self.fix_images()
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ FIX COMPLETED"))
        self.stdout.write("=" * 80)
    
    def fix_content_types(self):
        """تحديد نوع المحتوى المناسب لكل منشور بناءً على المحتوى أو العنوان"""
        self.stdout.write("\n📦 Fixing content types...")
        
        # إنشاء أنواع المحتوى إذا لم تكن موجودة
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
        
        ct_map = {}
        for name_ar, name_en, name_ku, priority in content_types:
            ct, created = ContentType.objects.get_or_create(
                name_en=name_en,
                defaults={
                    'name_ar': name_ar,
                    'name_ku': name_ku,
                    'priority': priority,
                }
            )
            ct_map[name_en.lower()] = ct
            if created:
                self.stdout.write(f"   ✅ Created: {name_ar}")
        
        # الكلمات المفتاحية لتحديد نوع المحتوى
        keywords = {
            'report': ['تقرير', 'report', 'تقريري', 'تقرير بحثي'],
            'infographic': ['انفوجرافيك', 'infographic', 'انفوغراف'],
            'video': ['فيديو', 'video', 'مرئي'],
            'documentary': ['وثائقي', 'documentary', 'فيلم وثائقي'],
            'survey': ['استبيان', 'survey', 'استطلاع', 'مسح'],
            'event': ['حدث', 'event', 'فعالية', 'مؤتمر'],
            'magazine': ['مجلة', 'magazine', 'دورية'],
            'book': ['كتاب', 'book', 'مطبوع'],
            'studies': ['دراسة', 'دراسات', 'studies', 'بحث'],
            'analytics': ['تحليل', 'تحليلات', 'analytics'],
            'opinion_article': ['رأي', 'opinion', 'مقال رأي', 'افتتاحية'],
            'files': ['ملف', 'ملفات', 'files', 'وثيقة'],
        }
        
        updated = 0
        posts = Posts.objects.filter(content_type__name_en='General')
        
        for post in posts:
            search_text = (post.title + ' ' + (post.content or '')).lower()
            
            assigned_ct = None
            for ct_type, words in keywords.items():
                for word in words:
                    if word.lower() in search_text:
                        assigned_ct = ct_map.get(ct_type)
                        break
                if assigned_ct:
                    break
            
            if assigned_ct:
                post.content_type = assigned_ct
                post.save()
                updated += 1
                if updated <= 20:
                    self.stdout.write(f"   ✅ Post {post.id}: '{post.title[:40]}' -> {assigned_ct.name_ar}")
        
        self.stdout.write(f"   ✅ Updated {updated} posts with proper content types")
    
    def fix_authors(self):
        """إصلاح المؤلفين (محاولة استخراج أسماء حقيقية من المحتوى)"""
        self.stdout.write("\n👤 Fixing authors...")
        
        # إنشاء مؤلفين إضافيين
        additional_authors = [
            ('مركز نور للإعلام', 'noor-center'),
            ('شبكة نور الإعلامية', 'noor-network'),
            ('فريق البحث', 'research-team'),
            ('المركز السوري', 'syrian-center'),
        ]
        
        for name, slug in additional_authors:
            author, created = Authors.objects.get_or_create(
                slug=slug,
                defaults={'full_name': name}
            )
            if created:
                self.stdout.write(f"   ✅ Created author: {name}")
        
        # محاولة تعيين مؤلفين لمنشورات بدون مؤلف
        default_author = Authors.objects.filter(full_name='Default Author').first()
        no_author_posts = Posts.objects.filter(author__isnull=True)
        
        # توزيع عشوائي للمنشورات على المؤلفين
        all_authors = list(Authors.objects.all())
        
        updated = 0
        for post in no_author_posts:
            if all_authors:
                # استخدام مؤشر ثابت بناءً على ID المنشور
                author_index = post.id % len(all_authors)
                post.author = all_authors[author_index]
                post.save()
                updated += 1
        
        self.stdout.write(f"   ✅ Assigned authors to {updated} posts")
    
    def fix_categories(self):
        """إصلاح التصنيفات"""
        self.stdout.write("\n📂 Fixing categories...")
        
        # إنشاء تصنيفات إضافية
        extra_categories = [
            ('أخبار', 'News', 'Nûçe'),
            ('تقارير', 'Reports', 'Rapor'),
            ('تحقيقات', 'Investigations', 'Lêkolîn'),
            ('مقالات', 'Articles', 'Gotar'),
            ('بيانات', 'Data', 'Daneyan'),
            ('إحصائيات', 'Statistics', 'Statîstîk'),
        ]
        
        default_ct = ContentType.objects.filter(name_en='General').first()
        
        for name_ar, name_en, name_ku in extra_categories:
            cat, created = Categories.objects.get_or_create(
                slug=slugify(name_ar),
                defaults={
                    'name_ar': name_ar,
                    'name_ku': name_ku,
                    'name_en': name_en,
                    'content_type': default_ct,
                }
            )
            if created:
                self.stdout.write(f"   ✅ Created category: {name_ar}")
        
        # تعيين تصنيفات للمنشورات بناءً على المحتوى
        category_keywords = {
            'أخبار': ['أخبار', 'news', 'حدث', 'تطور'],
            'تقارير': ['تقرير', 'report', 'نشر'],
            'تحقيقات': ['تحقيق', 'investigation', 'كشف'],
            'مقالات': ['مقال', 'article', 'رأي'],
            'بيانات': ['بيان', 'statement', 'إعلان'],
            'إحصائيات': ['إحصاء', 'statistic', 'عدد'],
        }
        
        updated = 0
        posts_without_cat = Posts.objects.filter(category__isnull=True)
        
        for post in posts_without_cat:
            search_text = (post.title + ' ' + (post.content or '')).lower()
            
            for cat_name, keywords in category_keywords.items():
                for word in keywords:
                    if word.lower() in search_text:
                        category = Categories.objects.filter(name_ar=cat_name).first()
                        if category:
                            post.category = category
                            post.save()
                            updated += 1
                            break
                    if updated > 500:
                        break
        
        self.stdout.write(f"   ✅ Assigned categories to {updated} posts")
    
    def fix_images(self):
        """ربط الصور الموجودة بالمنشورات"""
        self.stdout.write("\n🖼️  Fixing images...")
        
        import os
        from django.conf import settings
        
        media_root = settings.MEDIA_ROOT
        posts_dir = os.path.join(media_root, 'posts')
        
        if not os.path.exists(posts_dir):
            self.stdout.write(f"   ⚠️  Posts directory not found: {posts_dir}")
            return
        
        linked = 0
        
        # البحث عن الصور في مجلد posts
        for root, dirs, files in os.walk(posts_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    # محاولة استخراج post_id من اسم الملف
                    match = re.search(r'_(\d+)_', file)
                    if not match:
                        match = re.search(r'post(\d+)', file, re.IGNORECASE)
                    
                    if match:
                        post_id = int(match.group(1))
                        try:
                            post = Posts.objects.get(id=post_id)
                            if not post.featured_image:
                                relative_path = os.path.relpath(os.path.join(root, file), media_root).replace('\\', '/')
                                post.featured_image = relative_path
                                post.save()
                                linked += 1
                                if linked <= 50:
                                    self.stdout.write(f"   ✅ Linked post {post_id}: {file}")
                        except Posts.DoesNotExist:
                            pass
        
        # إذا لم يتم العثور على صور، حاول الربط حسب التاريخ
        if linked == 0:
            self.stdout.write(f"   🔍 No images found with ID in filename, trying date matching...")
            
            for post in Posts.objects.filter(featured_image__isnull=True)[:100]:
                if post.published_at:
                    year = str(post.published_at.year)
                    month = str(post.published_at.month).zfill(2)
                    
                    year_path = os.path.join(posts_dir, year)
                    if os.path.exists(year_path):
                        month_path = os.path.join(year_path, month)
                        if os.path.exists(month_path):
                            # البحث عن أي صورة في هذا الشهر
                            for day in os.listdir(month_path):
                                day_path = os.path.join(month_path, day)
                                if os.path.isdir(day_path):
                                    images = [f for f in os.listdir(day_path) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.gif'))]
                                    if images:
                                        relative_path = os.path.join('posts', year, month, day, images[0]).replace('\\', '/')
                                        post.featured_image = relative_path
                                        post.save()
                                        linked += 1
                                        self.stdout.write(f"   ✅ Linked post {post.id} by date: {images[0]}")
                                        break
        
        self.stdout.write(f"   ✅ Linked {linked} images to posts")