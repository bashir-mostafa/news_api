import os
import re
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from content.models import Posts, MediaFiles, MediaFileType
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class Command(BaseCommand):
    help = 'Extract and migrate images from post content to featured_image and MediaFiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--post-id',
            type=int,
            help='Process only specific post ID',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Process all posts (even those with featured_image)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        post_id = options.get('post_id')
        fix_all = options.get('fix_all')
        media_root = settings.MEDIA_ROOT

        # جلب المنشورات
        if post_id:
            posts = Posts.objects.filter(id=post_id)
        elif fix_all:
            posts = Posts.objects.all()
            self.stdout.write(self.style.WARNING("⚠️ Fixing ALL posts (including those with featured images)"))
        else:
            posts = Posts.objects.filter(featured_image__isnull=True)

        self.stdout.write(f"Found {posts.count()} posts to process\n")

        migrated_featured = 0
        migrated_content = 0
        media_files_created = 0
        no_images = 0
        errors = 0
        already_organized = 0

        for post in posts:
            self.stdout.write(f"\n📄 Processing Post {post.id}: {post.title[:60]}...")
            
            post_modified = False
            images_found = []
            
            # 1. معالجة الصورة المميزة (إذا كانت موجودة)
            if post.featured_image:
                result = self.migrate_single_image(
                    post.featured_image, 
                    post, 
                    media_root, 
                    dry_run,
                    'featured'
                )
                if result:
                    new_path, status, old_path, media_file = result
                    if status == 'migrated':
                        if not dry_run:
                            post.featured_image = new_path
                            post_modified = True
                            if media_file:
                                media_files_created += 1
                        migrated_featured += 1
                        self.stdout.write(self.style.SUCCESS(f"  ✅ Featured image migrated & saved to MediaFiles"))
                    elif status == 'already_organized':
                        already_organized += 1
                        self.stdout.write(f"  ℹ️ Featured image already organized")
                    elif status == 'error':
                        errors += 1
                        self.stdout.write(self.style.ERROR(f"  ❌ Featured image error"))
            
            # 2. معالجة الصور داخل المحتوى
            if post.content:
                new_content, count, found_images, media_files_list = self.migrate_images_in_content(
                    post.content, 
                    post, 
                    media_root, 
                    dry_run
                )
                if count > 0:
                    migrated_content += count
                    media_files_created += len(media_files_list)
                    images_found.extend(found_images)
                    if not dry_run:
                        post.content = new_content
                        post_modified = True
                    self.stdout.write(f"  ✅ Updated {count} image(s) in content and saved to MediaFiles")
                elif count == 0:
                    pass
            
            # حفظ التغييرات
            if post_modified and not dry_run:
                post.save(update_fields=['featured_image', 'content'])
                self.stdout.write(self.style.SUCCESS(f"  💾 Saved changes for post {post.id}"))
            elif post_modified and dry_run:
                self.stdout.write(self.style.WARNING(f"  🔍 DRY RUN: Would save changes"))
            
            if not images_found and not post.featured_image:
                no_images += 1

        # التقرير النهائي
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"Featured images migrated    : {migrated_featured}"))
        self.stdout.write(self.style.SUCCESS(f"Content images migrated     : {migrated_content}"))
        self.stdout.write(self.style.SUCCESS(f"MediaFiles records created  : {media_files_created}"))
        self.stdout.write(self.style.WARNING(f"Already organized           : {already_organized}"))
        self.stdout.write(self.style.WARNING(f"No images found             : {no_images}"))
        self.stdout.write(self.style.ERROR(f"Errors                      : {errors}"))

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No actual changes were made."))

    def migrate_single_image(self, image_path, post, media_root, dry_run, image_type):
        """ترحيل صورة واحدة وحفظها في MediaFiles"""
        if not image_path:
            return None
        
        image_path = str(image_path)
        
        # تحقق إذا كانت الصورة بالفعل في الهيكل الجديد
        parts = image_path.replace("\\", "/").split("/")
        if len(parts) >= 5 and parts[0] == 'posts' and len(parts[3]) == 2:
            return image_path, 'already_organized', None, None
        
        # استخراج اسم الملف
        filename = os.path.basename(image_path)
        
        # تحديد التاريخ للمسار الجديد
        ref_date = post.published_at or post.created_at
        if not ref_date:
            ref_date = datetime.now()
        
        year = ref_date.year
        month = str(ref_date.month).zfill(2)
        day = str(ref_date.day).zfill(2)
        
        # البحث عن الصورة في المسارات المحتملة
        old_abs_path = self.find_image_file(image_path, filename, media_root)
        
        if not old_abs_path:
            return None, 'error', image_path, None
        
        # المسار الجديد
        new_relative = f"posts/{year}/{month}/{day}/{filename}"
        new_abs = os.path.join(media_root, new_relative)
        
        # تحقق إذا كانت الصورة موجودة بالفعل
        if os.path.exists(new_abs):
            # تحديث أو إنشاء MediaFile
            media_file = self.create_or_update_media_file(post, new_relative, filename, dry_run)
            return new_relative, 'already_organized', old_abs_path, media_file
        
        self.stdout.write(f"  📸 {image_type}: {filename} → {year}/{month}/{day}/")
        
        media_file = None
        if not dry_run:
            os.makedirs(os.path.dirname(new_abs), exist_ok=True)
            shutil.copy2(old_abs_path, new_abs)
            
            # إنشاء سجل في MediaFiles
            media_file = self.create_or_update_media_file(post, new_relative, filename, dry_run)
        
        return new_relative, 'migrated', old_abs_path, media_file

    def migrate_images_in_content(self, content, post, media_root, dry_run):
        """معالجة الصور داخل المحتوى وحفظها في MediaFiles"""
        import warnings
        from bs4 import MarkupResemblesLocatorWarning
        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
        
        soup = BeautifulSoup(content, 'html.parser')
        images = soup.find_all('img')
        modified_count = 0
        found_images = []
        media_files_list = []
        
        for img in images:
            src = img.get('src', '')
            if not src:
                continue
            
            filename = os.path.basename(src)
            
            # تحقق إذا كانت الصورة في المسار الجديد بالفعل
            if '/media/posts/' in src and len(src.split('/')) >= 7:
                # تحديث أو إنشاء MediaFile للمسار الموجود
                relative_path = src.replace('/media/', '')
                media_file = self.create_or_update_media_file(post, relative_path, filename, dry_run)
                if media_file:
                    media_files_list.append(media_file)
                continue
            
            # البحث عن الصورة
            image_file_path = self.find_image_file(src, filename, media_root)
            
            if image_file_path:
                # تحديد التاريخ للمسار الجديد
                ref_date = post.published_at or post.created_at
                if not ref_date:
                    ref_date = datetime.now()
                
                year = ref_date.year
                month = str(ref_date.month).zfill(2)
                day = str(ref_date.day).zfill(2)
                
                new_relative = f"posts/{year}/{month}/{day}/{filename}"
                new_abs = os.path.join(media_root, new_relative)
                
                if not dry_run:
                    os.makedirs(os.path.dirname(new_abs), exist_ok=True)
                    if not os.path.exists(new_abs):
                        shutil.copy2(image_file_path, new_abs)
                    
                    # إنشاء سجل في MediaFiles
                    media_file = self.create_or_update_media_file(post, new_relative, filename, dry_run)
                    if media_file:
                        media_files_list.append(media_file)
                
                # تحديث الرابط في HTML
                new_src = f'/media/{new_relative}'
                img['src'] = new_src
                modified_count += 1
                found_images.append(filename)
                self.stdout.write(f"    🔄 Updated: {filename} → {year}/{month}/{day}/")
            else:
                # حاول تحميل الصورة إذا كان الرابط كاملاً
                if src.startswith('http') and 'nrls.net' in src:
                    self.stdout.write(f"    ⚠️ Image not found locally: {filename}")
        
        if modified_count > 0:
            return str(soup), modified_count, found_images, media_files_list
        return content, 0, [], media_files_list

    def create_or_update_media_file(self, post, file_path, filename, dry_run):
        """إنشاء أو تحديث سجل في MediaFiles"""
        if dry_run:
            return None
        
        try:
            # تحقق إذا كان السجل موجود مسبقاً
            media_file, created = MediaFiles.objects.get_or_create(
                post=post,
                src=file_path,
                defaults={
                    'file_type': MediaFileType.IMAGE,
                    'alt_text': filename,
                    'caption': f"Image for post: {post.title[:50]}",
                }
            )
            
            if not created and media_file.file_type != MediaFileType.IMAGE:
                media_file.file_type = MediaFileType.IMAGE
                media_file.save()
            
            return media_file
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"    ❌ Failed to create MediaFile: {str(e)}"))
            return None

    def find_image_file(self, image_ref, filename, media_root):
        """البحث عن ملف الصورة في جميع المسارات المحتملة"""
        
        # إذا كان image_ref مساراً مباشراً
        if os.path.exists(image_ref):
            return image_ref
        
        # قائمة المسارات للبحث
        search_paths = [
            os.path.join(media_root, 'posts', filename),
            os.path.join(media_root, filename),
            os.path.join(media_root, 'uploads', filename),
            os.path.join(media_root, 'old_uploads', filename),
            os.path.join(media_root, 'media_files', filename),
            os.path.join(media_root, 'images', filename),
        ]
        
        # البحث في مجلد posts بكل التواريخ
        posts_dir = os.path.join(media_root, 'posts')
        if os.path.exists(posts_dir):
            for root, dirs, files in os.walk(posts_dir):
                if filename in files:
                    return os.path.join(root, filename)
        
        # البحث في مجلد uploads
        uploads_dir = os.path.join(media_root, 'uploads')
        if os.path.exists(uploads_dir):
            for root, dirs, files in os.walk(uploads_dir):
                if filename in files:
                    return os.path.join(root, filename)
        
        # البحث في كل media
        if os.path.exists(media_root):
            for root, dirs, files in os.walk(media_root):
                if filename in files:
                    return os.path.join(root, filename)
        
        # البحث عن المسار من الرابط القديم
        if 'nrls.net' in image_ref:
            match = re.search(r'wp-content/uploads/(.+)$', image_ref)
            if match:
                relative_path = match.group(1)
                possible_path = os.path.join(media_root, 'old_uploads', relative_path)
                if os.path.exists(possible_path):
                    return possible_path
                
                possible_path = os.path.join(media_root, relative_path)
                if os.path.exists(possible_path):
                    return possible_path
        
        # البحث في جميع المسارات
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        return None