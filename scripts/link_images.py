# scripts/link_images.py
import os
import re
from django.conf import settings
from content.models import Posts

def link_images():
    media_root = settings.MEDIA_ROOT
    posts_dir = os.path.join(media_root, 'posts')
    
    print("=" * 60)
    print("🔗 LINKING IMAGES TO POSTS")
    print("=" * 60)
    
    if not os.path.exists(posts_dir):
        print(f"❌ Posts directory not found: {posts_dir}")
        return
    
    # جمع كل المنشورات بدون صور
    posts_without_images = Posts.objects.filter(featured_image__isnull=True)
    print(f"📝 Posts without images: {posts_without_images.count()}")
    
    # جمع كل الصور الموجودة
    images = []
    for root, dirs, files in os.walk(posts_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                rel_path = os.path.relpath(os.path.join(root, file), media_root).replace('\\', '/')
                images.append({
                    'path': rel_path,
                    'filename': file,
                    'full_path': os.path.join(root, file)
                })
    
    print(f"🖼️  Images found: {len(images)}")
    
    # طريقة 1: البحث عن post_id في اسم الصورة
    linked_by_id = 0
    for post in posts_without_images:
        for img in images:
            # بحث عن _postID_ أو postID في اسم الملف
            match = re.search(r'_(\d+)_', img['filename'])
            if not match:
                match = re.search(r'post(\d+)', img['filename'], re.IGNORECASE)
            
            if match and int(match.group(1)) == post.id:
                post.featured_image = img['path']
                post.save()
                linked_by_id += 1
                print(f"   ✅ Post {post.id} linked by ID: {img['filename']}")
                break
    
    print(f"\n📊 Linked by ID: {linked_by_id}")
    
    # طريقة 2: الربط حسب التاريخ (للباقي)
    remaining_posts = Posts.objects.filter(featured_image__isnull=True)
    linked_by_date = 0
    
    for post in remaining_posts:
        if post.published_at:
            year = str(post.published_at.year)
            month = str(post.published_at.month).zfill(2)
            
            # البحث عن صورة في نفس السنة والشهر
            for img in images:
                if f'/posts/{year}/{month}/' in img['path']:
                    post.featured_image = img['path']
                    post.save()
                    linked_by_date += 1
                    print(f"   ✅ Post {post.id} linked by date: {img['filename']}")
                    break
    
    print(f"\n📊 Linked by date: {linked_by_date}")
    
    # النتيجة النهائية
    total_with_images = Posts.objects.filter(featured_image__isnull=False).count()
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"   Total posts with images: {total_with_images}")
    print(f"   Linked by ID: {linked_by_id}")
    print(f"   Linked by date: {linked_by_date}")
    print("=" * 60)

if __name__ == "__main__":
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_api.settings')
    django.setup()
    link_images()