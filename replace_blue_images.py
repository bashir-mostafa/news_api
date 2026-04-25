# fast_replace.py
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_api.settings')
django.setup()

from content.models import Posts
from django.conf import settings
import shutil
from collections import defaultdict

# جمع الصور المحلية حسب التاريخ
images_by_date = defaultdict(list)
media_root = settings.MEDIA_ROOT
posts_dir = os.path.join(media_root, 'posts')

print("Scanning local images...")
for root, dirs, files in os.walk(posts_dir):
    for file in files:
        if file.lower().endswith(('.jpg', '.png', '.jpeg')) and not file.startswith('post_'):
            rel = os.path.relpath(os.path.join(root, file), media_root)
            parts = rel.split(os.sep)
            if len(parts) >= 4:
                date_key = f"{parts[1]}-{parts[2]}-{parts[3]}"
                images_by_date[date_key].append({
                    'path': os.path.join(root, file),
                    'rel': rel,
                    'file': file
                })

print(f"Found {sum(len(v) for v in images_by_date.values())} real images")

# معالجة المنشورات
posts = Posts.objects.all()
replaced = 0

for post in posts:
    if post.featured_image and 'post_' in str(post.featured_image):
        ref_date = post.published_at or post.created_at
        if ref_date:
            date_key = f"{ref_date.year}-{str(ref_date.month).zfill(2)}-{str(ref_date.day).zfill(2)}"
            
            if date_key in images_by_date and images_by_date[date_key]:
                img = images_by_date[date_key][0]
                new_path = f"posts/{date_key.replace('-', '/')}/{img['file']}"
                
                # نسخ إذا لزم الأمر
                target = os.path.join(media_root, new_path)
                if not os.path.exists(target):
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    shutil.copy2(img['path'], target)
                
                post.featured_image = new_path
                post.save()
                replaced += 1
                
                if replaced % 100 == 0:
                    print(f"Processed {replaced} posts...")

print(f"\n✅ Replaced {replaced} blue images with real ones!")