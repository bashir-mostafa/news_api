# run_this_in_shell.py
import os
import random
import shutil
from django.conf import settings
from content.models import Posts
from collections import defaultdict
from datetime import datetime

media_root = settings.MEDIA_ROOT
posts_dir = os.path.join(media_root, 'posts')

print("=" * 60)
print("DISTRIBUTING DIFFERENT IMAGES BY YEAR")
print("=" * 60)


print("\n📸 Scanning all existing images...")

images_by_year = defaultdict(list)

for root, dirs, files in os.walk(posts_dir):
    for file in files:
        if file.lower().endswith(('.jpg', '.png', '.jpeg', '.gif')):
            if file.startswith('post_'):
                continue
            
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, media_root)
            parts = rel_path.split(os.sep)
            
            year = parts[1] if len(parts) > 1 else 'unknown'
            
            images_by_year[year].append({
                'path': full_path,
                'rel': rel_path,
                'file': file,
                'year': year
            })

print(f"✅ Found images in years: {sorted(images_by_year.keys())}")
for year, images in images_by_year.items():
    print(f"   {year}: {len(images)} images")

# ============================================
# 2. توزيع صور مختلفة لكل منشور
# ============================================
posts = Posts.objects.all()
total_posts = posts.count()

print(f"\n📄 Total posts: {total_posts}")
print("🔄 Assigning different images...\n")

replaced = 0
no_images = 0

image_index = 0
all_images = []
for year, images in images_by_year.items():
    all_images.extend(images)

if not all_images:
    print("❌ No images found!")
else:
    for post in posts:
        ref_date = post.published_at or post.created_at
        if not ref_date:
            ref_date = datetime.now()
        
        post_year = str(ref_date.year)
        
        if post_year in images_by_year and images_by_year[post_year]:
            matched_image = random.choice(images_by_year[post_year])
            source = f"same year ({post_year})"
        else:
            matched_image = random.choice(all_images)
            source = f"random (from {matched_image['year']})"
        
        year = post_year
        month = str(ref_date.month).zfill(2)
        day = str(ref_date.day).zfill(2)
        
        base_name = os.path.splitext(matched_image['file'])[0]
        ext = os.path.splitext(matched_image['file'])[1]
        new_filename = f"{base_name}_post{post.id}{ext}"
        
        new_rel_path = f"posts/{year}/{month}/{day}/{new_filename}"
        new_abs_path = os.path.join(media_root, new_rel_path)
        
        os.makedirs(os.path.dirname(new_abs_path), exist_ok=True)
        shutil.copy2(matched_image['path'], new_abs_path)
        
        post.featured_image = new_rel_path
        post.save()
        
        replaced += 1
        
        if replaced % 100 == 0:
            print(f"  ✅ Processed {replaced}/{total_posts} posts...")

print("\n" + "=" * 60)
print("📊 FINAL SUMMARY")
print("=" * 60)
print(f"✅ Updated: {replaced} posts")
print(f"📁 Using {len(all_images)} different source images")
print("=" * 60)