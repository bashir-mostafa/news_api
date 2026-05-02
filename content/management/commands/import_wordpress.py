# content/management/commands/import_wordpress.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.core.files import File
from content.models import (
    ContentType, Authors, Categories, Tags, Posts, Comments,
    Language, MediaFiles
)
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

class Command(BaseCommand):
    help = 'Import WordPress data with images'
    
    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data')
        parser.add_argument('--dry-run', action='store_true', help='Dry run')
        parser.add_argument('--limit', type=int, default=0, help='Limit posts')
        parser.add_argument('--media-dir', type=str, default='media', help='Media directory path')
    
    def handle(self, *args, **options):
        clear_existing = options['clear']
        dry_run = options['dry_run']
        limit = options['limit']
        media_dir = options['media_dir']
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("🚀 IMPORTING WORDPRESS DATA WITH IMAGES"))
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  DRY RUN MODE - No data will be saved"))
        
        if clear_existing and not dry_run:
            self.clear_existing_data()
        
        # استخراج جميع البيانات
        all_data = self.extract_all_data_streaming()
        
        if not all_data['posts']:
            self.stdout.write(self.style.ERROR("\n❌ No posts found!"))
            return
        
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"   Posts: {len(all_data['posts'])}")
        self.stdout.write(f"   Images: {len(all_data['images'])}")
        
        if dry_run:
            self.print_dry_run_summary(all_data)
            return
        
        # استيراد البيانات مع الصور
        with transaction.atomic():
            self.import_content_types()
            self.import_static_categories()
            self.import_authors()
            self.import_posts_with_images(all_data, limit, media_dir)
        
        self.print_final_summary()
    
    def extract_all_data_streaming(self):
        """استخراج جميع البيانات (منشورات + صور)"""
        
        sql_files = ["i5218891_wp4.sql", "i5218891_wp9.sql", "i7736595_wp1.sql"]
        all_data = {
            'posts': [],
            'images': [],
            'post_images': {},  # post_id -> image_id
            'attachments': {},  # attachment_id -> image_data
        }
        
        for sql_file in sql_files:
            if not os.path.exists(sql_file):
                continue
            
            file_size_mb = os.path.getsize(sql_file) / 1024 / 1024
            self.stdout.write(f"\n📄 Reading: {sql_file} ({file_size_mb:.1f} MB)")
            
            data = self.extract_data_from_file(sql_file)
            all_data['posts'].extend(data['posts'])
            
            # جمع معلومات الصور
            for img_id, img_data in data['attachments'].items():
                if img_id not in all_data['attachments']:
                    all_data['attachments'][img_id] = img_data
            
            # جمع علاقات الصور بالمنشورات
            for post_id, img_id in data['post_images'].items():
                all_data['post_images'][post_id] = img_id
            
            self.stdout.write(f"   ✅ Posts: {len(data['posts'])}, Images: {len(data['attachments'])}")
        
        return all_data
    
    def extract_data_from_file(self, filepath):
        """استخراج البيانات من ملف واحد"""
        
        data = {
            'posts': [],
            'attachments': {},
            'post_images': {},
        }
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 1. استخراج wp_posts
        post_pattern = r"INSERT INTO `wp_posts` \(.*?\) VALUES\s*\((.*?)\);"
        matches = re.findall(post_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            values = self.parse_row(match)
            if len(values) >= 20:
                post_type = self.clean_value(values[20]) if len(values) > 20 else 'post'
                
                # تخزين الصور المرفقة (attachments)
                if post_type == 'attachment':
                    attachment_id = self.clean_value(values[0])
                    attachment_url = self.clean_value(values[3]) if len(values) > 3 else ''  # guid
                    attachment_mime = self.clean_value(values[21]) if len(values) > 21 else ''
                    parent_post = self.clean_value(values[17]) if len(values) > 17 else 0  # post_parent
                    
                    if attachment_id and attachment_url:
                        data['attachments'][attachment_id] = {
                            'id': attachment_id,
                            'url': attachment_url,
                            'mime_type': attachment_mime,
                            'parent_post': parent_post,
                        }
                
                # تخزين المنشورات العادية
                elif post_type in ['post', 'page']:
                    post = {
                        'id': self.clean_value(values[0]),
                        'author': self.clean_value(values[1]),
                        'date': self.clean_value(values[2]),
                        'content': self.clean_value(values[4]) if len(values) > 4 else '',
                        'title': self.clean_value(values[5]) if len(values) > 5 else '',
                        'excerpt': self.clean_value(values[6]) if len(values) > 6 else '',
                        'status': self.clean_value(values[7]) if len(values) > 7 else 'publish',
                        'post_type': post_type,
                    }
                    if post['title'] or post['content']:
                        data['posts'].append(post)
        
        # 2. استخراج wp_postmeta (_thumbnail_id)
        meta_pattern = r"INSERT INTO `wp_postmeta` \(.*?\) VALUES\s*\((.*?)\);"
        matches = re.findall(meta_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            values = self.parse_row(match)
            if len(values) >= 4:
                post_id = self.clean_value(values[1])
                meta_key = self.clean_value(values[2])
                meta_value = self.clean_value(values[3])
                
                if meta_key == '_thumbnail_id' and post_id and meta_value:
                    data['post_images'][post_id] = meta_value
        
        return data
    
    def parse_row(self, row_str):
        """تفكيك صف من القيم"""
        values = []
        current = ''
        in_string = False
        escape = False
        
        for char in row_str:
            if escape:
                current += char
                escape = False
            elif char == '\\':
                escape = True
                current += char
            elif char == "'" and not in_string:
                in_string = True
                current += char
            elif char == "'" and in_string:
                in_string = False
                current += char
            elif char == ',' and not in_string:
                values.append(current.strip())
                current = ''
            else:
                current += char
        
        if current:
            values.append(current.strip())
        
        return values
    
    def clean_value(self, val):
        """تنظيف القيمة"""
        if not val or val.upper() == 'NULL':
            return None
        if val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        val = val.replace("\\'", "'").replace('\\"', '"')
        val = val.replace("\\n", "\n").replace("\\r", "\r")
        return val.strip()
    
    def clear_existing_data(self):
        """مسح البيانات الموجودة"""
        self.stdout.write("\n🗑️  Clearing existing data...")
        MediaFiles.objects.all().delete()
        Comments.objects.all().delete()
        Posts.objects.all().delete()
        Tags.objects.all().delete()
        Categories.objects.all().delete()
        Authors.objects.all().delete()
        ContentType.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("   ✅ Cleared"))
    
    def import_content_types(self):
        """إنشاء ContentType"""
        self.stdout.write("\n📦 Creating content types...")
        ct, _ = ContentType.objects.get_or_create(
            name_en='General',
            defaults={'name_ar': 'عام', 'name_ku': 'Giştî', 'priority': 1}
        )
        self.stdout.write(f"   ✅ Created: {ct.name_ar}")
    
    def import_static_categories(self):
        """إنشاء التصنيفات الثابتة"""
        self.stdout.write("\n📂 Creating static categories...")
        
        categories = [
            'إنفوجرافيك', 'فيديو', 'وثائقي', 'تقرير', 'استبيان',
            'حدث', 'مجلة', 'كتاب', 'دراسات', 'تحليلات', 'مقال رأي', 'ملفات'
        ]
        
        default_ct = ContentType.objects.first()
        created = 0
        
        for name in categories:
            cat, c = Categories.objects.get_or_create(
                slug=slugify(name)[:255],
                defaults={
                    'name_ar': name, 'name_ku': name, 'name_en': name,
                    'content_type': default_ct
                }
            )
            if c:
                created += 1
                self.stdout.write(f"   ✅ {name}")
        
        self.stdout.write(f"   ✅ Created {created} categories")
    
    def import_authors(self):
        """إنشاء مؤلف افتراضي"""
        self.stdout.write("\n👤 Creating default author...")
        author, _ = Authors.objects.get_or_create(
            full_name='Default Author',
            defaults={'slug': 'default-author'}
        )
        self.stdout.write(f"   ✅ {author.full_name}")
    
    def import_posts_with_images(self, all_data, limit, media_dir):
        """استيراد المنشورات مع الصور"""
        self.stdout.write("\n📝 Importing posts with images...")
        
        default_ct = ContentType.objects.first()
        default_lang = Language.KU
        default_author = Authors.objects.first()
        
        posts_to_import = all_data['posts'][:limit] if limit > 0 else all_data['posts']
        
        posts_created = 0
        pages_created = 0
        images_linked = 0
        images_copied = 0
        
        # إنشاء قاموس المراسلات بين ID القديم والجديد
        post_id_map = {}
        
        for post_data in posts_to_import:
            is_page = (post_data.get('post_type') == 'page')
            old_post_id = post_data.get('id')
            
            # تحويل التاريخ
            published_at = None
            if post_data.get('date'):
                try:
                    date_str = str(post_data['date'])
                    if date_str and len(date_str) >= 19:
                        naive_dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
                        published_at = timezone.make_aware(naive_dt)
                except:
                    pass
            
            title = (post_data.get('title') or 'Untitled')[:500]
            
            if Posts.objects.filter(title=title).exists():
                continue
            
            try:
                post = Posts.objects.create(
                    title=title,
                    content=post_data.get('content', ''),
                    excerpt=post_data.get('excerpt', '')[:500] if post_data.get('excerpt') else None,
                    published_at=published_at,
                    is_published=(post_data.get('status') == 'publish'),
                    language=default_lang,
                    content_type=default_ct,
                    author=default_author,
                    view_count=0,
                )
                
                # حفظ المراسلة
                if old_post_id:
                    post_id_map[old_post_id] = post.id
                
                if is_page:
                    pages_created += 1
                else:
                    posts_created += 1
                
                # معالجة الصورة المميزة
                featured_image_id = all_data['post_images'].get(old_post_id)
                if featured_image_id and featured_image_id in all_data['attachments']:
                    image_data = all_data['attachments'][featured_image_id]
                    image_url = image_data.get('url', '')
                    
                    if image_url:
                        # محاولة ربط الصورة
                        linked = self.link_image_to_post(post, image_url, media_dir)
                        if linked:
                            images_linked += 1
                            images_copied += linked
                
                total = posts_created + pages_created
                if total % 50 == 0:
                    self.stdout.write(f"   ... {total} imported, {images_linked} images")
                    
            except Exception as e:
                self.stdout.write(f"   ⚠️  Error: {str(e)[:80]}")
        
        self.stdout.write(f"\n   ✅ Created {posts_created} posts, {pages_created} pages")
        self.stdout.write(f"   ✅ Linked {images_linked} featured images")
    
    # content/management/commands/import_wordpress.py (جزء الصور المعدل)

    def link_image_to_post(self, post, image_url, media_dir):
        """ربط الصورة بالمنشور وحفظها في مجلد حسب التاريخ"""
        filename = os.path.basename(image_url)
        if not filename:
            return 0
        
        media_root = media_dir
        
        # تحديد التاريخ المستخدم لحفظ الصورة
        # نستخدم تاريخ النشر إذا موجود، وإلا نستخدم التاريخ الحالي
        if post.published_at:
            year = str(post.published_at.year)
            month = str(post.published_at.month).zfill(2)
            day = str(post.published_at.day).zfill(2)
        else:
            now = datetime.now()
            year = now.strftime('%Y')
            month = now.strftime('%m')
            day = now.strftime('%d')
        
        # مسارات محتملة للصورة المصدر
        possible_paths = [
            os.path.join(media_root, filename),
            os.path.join(media_root, 'uploads', filename),
            os.path.join(media_root, 'uploads', year, month, filename),
            os.path.join(media_root, 'uploads', year, month, day, filename),
            os.path.join(media_root, 'wp-content', 'uploads', year, month, filename),
            os.path.join(media_root, 'wp-content', 'uploads', year, month, day, filename),
            os.path.join(media_root, 'posts', filename),
            os.path.join(media_root, 'posts', year, month, filename),
            os.path.join(media_root, 'posts', year, month, day, filename),
            os.path.join(media_root, 'media_files', filename),
        ]
        
        # البحث في مجلدات السنوات المختلفة (2019-2026)
        for yr in range(2019, 2027):
            possible_paths.append(os.path.join(media_root, 'posts', str(yr), filename))
            possible_paths.append(os.path.join(media_root, 'uploads', str(yr), filename))
            for mo in range(1, 13):
                month_str = str(mo).zfill(2)
                possible_paths.append(os.path.join(media_root, 'posts', str(yr), month_str, filename))
                possible_paths.append(os.path.join(media_root, 'uploads', str(yr), month_str, filename))
        
        # إزالة المسارات المكررة
        possible_paths = list(dict.fromkeys(possible_paths))
        
        # البحث عن الصورة
        for img_path in possible_paths:
            if os.path.exists(img_path):
                try:
                    # إنشاء اسم ملف جديد
                    ext = os.path.splitext(filename)[1]
                    # استخدام ID المنشور والتاريخ لإنشاء اسم فريد
                    safe_title = re.sub(r'[^a-zA-Z0-9]', '_', post.title[:30]) if post.title else 'post'
                    new_filename = f"{year}{month}{day}_{post.id}_{safe_title}{ext}"
                    
                    # إنشاء المسار الهدف مع التاريخ
                    target_dir = os.path.join(media_root, 'posts', year, month, day)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    new_file_path = os.path.join(target_dir, new_filename)
                    
                    # نسخ الصورة
                    shutil.copy2(img_path, new_file_path)
                    
                    # حفظ المسار النسبي في قاعدة البيانات
                    relative_path = os.path.join('posts', year, month, day, new_filename).replace('\\', '/')
                    post.featured_image = relative_path
                    post.save()
                    
                    self.stdout.write(f"      📸 Copied: {filename} -> {relative_path}")
                    return 1
                    
                except Exception as e:
                    self.stdout.write(f"      ⚠️  Copy error: {e}")
                    return 0
        
        return 0
    
    def print_dry_run_summary(self, all_data):
        """طباعة ملخص التجربة"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.WARNING("📊 DRY RUN SUMMARY"))
        self.stdout.write("=" * 80)
        
        posts_count = sum(1 for p in all_data['posts'] if p.get('post_type') == 'post')
        pages_count = sum(1 for p in all_data['posts'] if p.get('post_type') == 'page')
        
        self.stdout.write(f"   📝 Posts: {posts_count}")
        self.stdout.write(f"   📄 Pages: {pages_count}")
        self.stdout.write(f"   🖼️  Images in database: {len(all_data['attachments'])}")
        self.stdout.write(f"   🔗 Posts with featured images: {len(all_data['post_images'])}")
        self.stdout.write(f"   📂 Static categories: 12")
        
        # عرض عينة من الصور
        if all_data['attachments']:
            self.stdout.write(f"\n   📌 Sample images:")
            for i, (img_id, img_data) in enumerate(list(all_data['attachments'].items())[:5]):
                url = img_data.get('url', '')[:60]
                self.stdout.write(f"      {i+1}. ID: {img_id} - {url}")
    
    def print_final_summary(self):
        """طباعة الملخص النهائي"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ IMPORT COMPLETED"))
        self.stdout.write("=" * 80)
        
        posts_count = Posts.objects.count()
        posts_with_images = Posts.objects.filter(featured_image__isnull=False).count()
        
        self.stdout.write(f"   📝 Posts: {posts_count}")
        self.stdout.write(f"   🖼️  Posts with images: {posts_with_images}")
        self.stdout.write(f"   📂 Categories: {Categories.objects.count()}")
        self.stdout.write(f"   📦 Content Types: {ContentType.objects.count()}")
        
        if posts_with_images > 0:
            self.stdout.write(f"\n   ✅ Images successfully linked to {posts_with_images} posts")
        
        self.stdout.write("=" * 80)