"""
WordPress to Django Migration Command - Smart Matching
Run: python manage.py migrate_wordpress
"""

import os
import re
import random
import shutil
from datetime import datetime, timezone
from html import unescape
from collections import defaultdict
from difflib import SequenceMatcher

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.utils import timezone as tz
from tqdm import tqdm

from content.models import (
    Authors, Categories, Tags, Posts, Comments, 
    ContentType, MediaFiles
)

# ============================================================
# SETTINGS
# ============================================================

SQL_FILES = [
    "i5218891_wp4.sql",
    "i5218891_wp9.sql",
    "i7736595_wp1.sql",
]

DEFAULT_LANGUAGE = "ku"
DEFAULT_CONTENT_TYPE_ID = 1
NOW = datetime.now(timezone.utc)

# خريطة لمطابقة أنواع المحتوى العربية مع ContentType
CONTENT_TYPE_MAPPING = {
    'infographic': ['انفوجرافيك', 'انفوغرافيك', 'infographic', 'انفوجراف'],
    'video': ['فيديو', 'video', 'مرئي', 'ڤيديو'],
    'documentary': ['وثائقي', 'documentary', 'تقرير', 'تقريري'],
    'report': ['تقرير', 'report', 'تقرير بحثي'],
    'survey': ['استبيان', 'survey', 'استطلاع', 'مسح'],
    'event': ['حدث', 'event', 'فعالية', 'نشاط'],
    'magazine': ['مجلة', 'magazine', 'دورية'],
    'book': ['كتاب', 'book', 'مطبوع'],
    'studies': ['دراسات', 'studies', 'بحث', 'دراسة'],
    'analytics': ['تحليلات', 'analytics', 'تحليل'],
    'opinion_article': ['مقال رأي', 'opinion', 'رأي', 'افتتاحية'],
    'files': ['ملفات', 'files', 'وثائق'],
}

# خريطة للغات
LANGUAGE_MAPPING = {
    'ar': ['ar', 'arabic', 'عربي', 'عربية'],
    'ku': ['ku', 'kurdish', 'كردي', 'كردية', 'kurdi'],
    'en': ['en', 'english', 'انجليزي', 'إنجليزي', 'english'],
}

# خريطة لحالات المنشور
STATUS_MAPPING = {
    'publish': ['publish', 'published', 'public', 'منشور', 'منشورة'],
    'draft': ['draft', 'drafted', 'مسودة', 'غير منشور'],
    'private': ['private', 'خاص', 'محمي'],
    'future': ['future', 'مستقبلي', 'جدولة'],
    'trash': ['trash', 'مهملات', 'محذوف'],
}

# ============================================================
# SMART MATCHING FUNCTIONS
# ============================================================

def smart_string_match(text1, text2, threshold=0.6):
    """مقارنة ذكية بين نصين"""
    if not text1 or not text2:
        return False
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    return SequenceMatcher(None, text1, text2).ratio() >= threshold

def find_best_match(text, mapping_dict, threshold=0.6):
    """البحث عن أفضل تطابق في القاموس"""
    if not text:
        return None
    
    text = text.lower().strip()
    
    # تطابق تام
    for key, values in mapping_dict.items():
        if text in values or text == key:
            return key
    
    # تطابق جزئي
    for key, values in mapping_dict.items():
        for value in values:
            if smart_string_match(text, value, threshold):
                return key
    
    return None

def parse_smart_date(date_string):
    """تحليل التاريخ بشكل ذكي"""
    if not date_string:
        return None
    
    if isinstance(date_string, datetime):
        return date_string
    
    try:
        # محاولة تحويل النص إلى تاريخ
        if isinstance(date_string, str):
            # تنسيقات مختلفة
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y',
                '%Y%m%d',
            ]
            for fmt in formats:
                try:
                    naive_dt = datetime.strptime(date_string, fmt)
                    return tz.make_aware(naive_dt)
                except:
                    continue
    except:
        pass
    
    return None

# ============================================================
# DIRECT SQL PARSING
# ============================================================

def parse_sql_dump(filepath):
    """Parse SQL dump file and extract ALL data from WordPress tables"""
    
    print(f"\n📄 Processing: {os.path.basename(filepath)}")
    
    data = {
        'wp_users': [],
        'wp_terms': [],
        'wp_term_taxonomy': [],
        'wp_term_relationships': [],
        'wp_posts': [],
        'wp_comments': [],
        'wp_postmeta': [],
        'wp_options': [],  # إضافة لقراءة إعدادات الموقع
    }
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    for table in data.keys():
        rows = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if f'INSERT INTO `{table}`' in line or f'INSERT INTO {table}' in line:
                insert_lines = [line]
                i += 1
                
                while i < len(lines) and ';' not in insert_lines[-1]:
                    insert_lines.append(lines[i])
                    i += 1
                
                full_insert = ' '.join(insert_lines)
                table_rows = extract_rows_from_insert(full_insert)
                rows.extend(table_rows)
            
            i += 1
        
        if rows:
            print(f"    {table}: {len(rows):,} rows")
            data[table] = rows
    
    return data

def extract_rows_from_insert(insert_sql):
    """Extract rows from an INSERT statement"""
    rows = []
    
    values_match = re.search(r'VALUES\s+(.*)$', insert_sql, re.IGNORECASE | re.DOTALL)
    if not values_match:
        return rows
    
    values_part = values_match.group(1).rstrip(';').strip()
    
    row_strings = []
    depth = 0
    current_row = []
    in_string = False
    escape_next = False
    
    for char in values_part:
        if escape_next:
            current_row.append(char)
            escape_next = False
        elif char == '\\':
            escape_next = True
            current_row.append(char)
        elif char == "'" and not in_string:
            in_string = True
            current_row.append(char)
        elif char == "'" and in_string:
            in_string = False
            current_row.append(char)
        elif char == '(' and not in_string:
            if depth == 0:
                current_row = []
            depth += 1
            current_row.append(char)
        elif char == ')' and not in_string:
            depth -= 1
            current_row.append(char)
            if depth == 0:
                row_strings.append(''.join(current_row))
        elif depth > 0:
            current_row.append(char)
    
    for row_str in row_strings:
        if row_str.startswith('(') and row_str.endswith(')'):
            row_str = row_str[1:-1]
        
        values = []
        current_value = []
        in_string = False
        escape_next = False
        
        for char in row_str:
            if escape_next:
                current_value.append(char)
                escape_next = False
            elif char == '\\':
                escape_next = True
                current_value.append(char)
            elif char == "'" and not in_string:
                in_string = True
                current_value.append(char)
            elif char == "'" and in_string:
                in_string = False
                current_value.append(char)
            elif char == ',' and not in_string:
                val = ''.join(current_value).strip()
                values.append(clean_value(val))
                current_value = []
            else:
                current_value.append(char)
        
        if current_value:
            val = ''.join(current_value).strip()
            values.append(clean_value(val))
        
        if values:
            rows.append(values)
    
    return rows

def clean_value(val):
    """Clean a single value"""
    if not val or val.upper() == 'NULL':
        return None
    
    if val.startswith("'") and val.endswith("'"):
        val = val[1:-1]
    
    val = val.replace("\\'", "'")
    val = val.replace('\\"', '"')
    val = val.replace("\\n", "\n")
    val = val.replace("\\r", "\r")
    val = val.replace("\\t", "\t")
    val = val.replace("\\\\", "\\")
    
    return val

# ============================================================
# DATA PROCESSING CLASS WITH SMART MATCHING
# ============================================================

class WordPressData:
    def __init__(self, raw_data, source_file):
        self.source = source_file
        self.raw = raw_data
        self.users = {}
        self.categories = []
        self.tags = []
        self.posts = []
        self.pages = []
        self.comments = []
        self.media_files = []
        self.post_terms = defaultdict(set)
        self.post_categories = {}
        self.site_options = {}  # إعدادات الموقع
        self.post_meta = defaultdict(dict)  # بيانات إضافية للمنشورات
        
        self._process()
    
    def _process(self):
        print(f"  Processing {os.path.basename(self.source)}...")
        
        # ===== Site Options =====
        for row in self.raw.get('wp_options', []):
            if len(row) >= 3:
                try:
                    option_name = str(row[1] or '')
                    option_value = str(row[2] or '')
                    self.site_options[option_name] = option_value
                except:
                    continue
        print(f"    Site options: {len(self.site_options)}")
        
        # ===== Users =====
        for row in self.raw.get('wp_users', []):
            if len(row) >= 10 and row[0]:
                try:
                    user_id = int(row[0])
                    self.users[user_id] = {
                        'id': user_id,
                        'login': str(row[1] or ''),
                        'email': str(row[4] or ''),
                        'display_name': str(row[9] or ''),
                        'nicename': str(row[3] or ''),
                        'registered': row[7] if len(row) > 7 else None,
                    }
                except:
                    continue
        print(f"    Users: {len(self.users)}")
        
        # ===== Post Meta =====
        for row in self.raw.get('wp_postmeta', []):
            if len(row) >= 4:
                try:
                    post_id = int(row[0]) if row[0] else 0
                    meta_key = str(row[1] or '')
                    meta_value = str(row[2] or '')
                    if post_id:
                        self.post_meta[post_id][meta_key] = meta_value
                except:
                    continue
        print(f"    Posts with meta: {len(self.post_meta)}")
        
        # ===== Term Taxonomy =====
        term_taxonomy = {}
        for row in self.raw.get('wp_term_taxonomy', []):
            if len(row) >= 4 and row[0]:
                try:
                    tt_id = int(row[0])
                    term_taxonomy[tt_id] = {
                        'term_id': int(row[1]) if row[1] else 0,
                        'taxonomy': str(row[2] or ''),
                        'description': str(row[3] or ''),
                        'parent': int(row[4]) if len(row) > 4 and row[4] else 0,
                    }
                except:
                    continue
        print(f"    Term taxonomy: {len(term_taxonomy)}")
        
        # ===== Terms =====
        terms = {}
        for row in self.raw.get('wp_terms', []):
            if len(row) >= 2 and row[0]:
                try:
                    term_id = int(row[0])
                    terms[term_id] = {
                        'name': str(row[1] or ''),
                        'slug': str(row[2] or '') if len(row) > 2 else '',
                    }
                except:
                    continue
        print(f"    Terms: {len(terms)}")
        
        # ===== Build Categories and Tags =====
        for tt in term_taxonomy.values():
            term_id = tt['term_id']
            if term_id in terms:
                term_data = {
                    'original_id': term_id,
                    'name': terms[term_id]['name'],
                    'slug': terms[term_id]['slug'],
                    'description': tt['description'],
                }
                if tt['taxonomy'] == 'category':
                    self.categories.append(term_data)
                elif tt['taxonomy'] == 'post_tag':
                    self.tags.append(term_data)
        
        print(f"    Categories: {len(self.categories)}")
        print(f"    Tags: {len(self.tags)}")
        
        # ===== Post-Term Relationships =====
        for row in self.raw.get('wp_term_relationships', []):
            if len(row) >= 2 and row[0]:
                try:
                    post_id = int(row[0])
                    tt_id = int(row[1])
                    if tt_id in term_taxonomy:
                        term_id = term_taxonomy[tt_id]['term_id']
                        taxonomy = term_taxonomy[tt_id]['taxonomy']
                        self.post_terms[post_id].add(term_id)
                        
                        if taxonomy == 'category':
                            self.post_categories[post_id] = term_id
                except:
                    continue
        print(f"    Posts with terms: {len(self.post_terms)}")
        
        # ===== Posts - SMART EXTRACTION =====
        for row in self.raw.get('wp_posts', []):
            if len(row) < 21:
                continue
            
            try:
                post_id = int(row[0]) if row[0] else 0
                if not post_id:
                    continue
                
                post_type = str(row[20]) if len(row) > 20 else 'post'
                post_status = str(row[7]) if len(row) > 7 else 'publish'
                
                title = str(row[5] or '').strip()
                if not title:
                    title = f"Untitled {post_type} (ID: {post_id})"
                
                # تحديد اللغة من محتوى المنشور أو من الإعدادات
                content_text = str(row[4] or '') + title
                detected_lang = self.detect_language(content_text)
                
                # تحديد نوع المحتوى
                content_type_slug = self.detect_content_type(content_text, title)
                
                # الحصول على الصورة المميزة من post_meta
                featured_image_id = self.post_meta.get(post_id, {}).get('_thumbnail_id')
                
                category_id = self.post_categories.get(post_id)
                
                # معالجة التاريخ مع المنطقة الزمنية
                post_date = parse_smart_date(row[2] if len(row) > 2 and row[2] else None)
                post_modified = parse_smart_date(row[14] if len(row) > 14 and row[14] else None)
                post_date_gmt = parse_smart_date(row[3] if len(row) > 3 and row[3] else None)
                
                post_data = {
                    'original_id': post_id,
                    'original_author': int(row[1]) if len(row) > 1 and row[1] else 0,
                    'title': unescape(title),
                    'content': str(row[4] or ''),
                    'excerpt': unescape(str(row[6] or '')).strip() if len(row) > 6 else None,
                    'status': post_status,
                    'status_display': self.map_status(post_status),
                    'post_type': post_type,
                    'published_at': post_date_gmt or post_date,
                    'created_at': post_date or NOW,
                    'updated_at': post_modified or NOW,
                    'category_id': category_id,
                    'term_ids': self.post_terms.get(post_id, set()),
                    'view_count': int(row[22]) if len(row) > 22 and row[22] else 0,
                    'detected_language': detected_lang,
                    'detected_content_type': content_type_slug,
                    'featured_image_id': featured_image_id,
                    'meta_data': self.post_meta.get(post_id, {}),
                    'guid': str(row[3]) if len(row) > 3 else None,
                }
                
                if post_type == 'page':
                    self.pages.append(post_data)
                elif post_type == 'attachment':
                    self.media_files.append({
                        'original_id': post_id,
                        'title': title,
                        'url': str(row[4] or ''),
                        'guid': str(row[3]) if len(row) > 3 else None,
                        'mime_type': str(row[21]) if len(row) > 21 else '',
                        'parent_post': int(row[2]) if len(row) > 2 and row[2] else None,
                    })
                else:
                    self.posts.append(post_data)
                    
            except Exception as e:
                continue
        
        print(f"    Posts: {len(self.posts)}")
        print(f"    Pages: {len(self.pages)}")
        print(f"    Media Files: {len(self.media_files)}")
        
        # ===== Comments =====
        for row in self.raw.get('wp_comments', []):
            if len(row) >= 11:
                try:
                    self.comments.append({
                        'post_id': int(row[1]) if row[1] else 0,
                        'name': str(row[2] or 'Anonymous').strip(),
                        'email': str(row[3] or '').strip(),
                        'content': str(row[8] or '').strip(),
                        'approved': str(row[10]) == '1' if len(row) > 10 else False,
                        'created_at': parse_smart_date(row[6] if len(row) > 6 else None) or NOW,
                    })
                except:
                    continue
        
        print(f"    Comments: {len(self.comments)}")
    
    def detect_language(self, text):
        """كشف اللغة من النص"""
        if not text:
            return DEFAULT_LANGUAGE
        
        text = text.lower()
        
        # كلمات عربية شائعة
        arabic_words = ['ال', 'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'و', 'ف']
        # كلمات كردية شائعة
        kurdish_words = ['û', 'bi', 'ji', 'li', 'di', 'ev', 'ew', 'ku', 'ye']
        
        arabic_count = sum(1 for word in arabic_words if word in text)
        kurdish_count = sum(1 for word in kurdish_words if word in text)
        
        # التحقق من وجود أحرف عربية
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', text))
        has_kurdish_chars = bool(re.search(r'[ێەڕۆڤگچژ]', text))
        
        if has_kurdish_chars or kurdish_count > arabic_count:
            return 'ku'
        elif has_arabic or arabic_count > 0:
            return 'ar'
        else:
            return 'en'
    
    def detect_content_type(self, content, title):
        """كشف نوع المحتوى من النص والعنوان"""
        search_text = (title + ' ' + content).lower()
        
        for content_type, keywords in CONTENT_TYPE_MAPPING.items():
            for keyword in keywords:
                if keyword.lower() in search_text:
                    return content_type
        
        return None
    
    def map_status(self, status):
        """تحويل حالة المنشور"""
        if not status:
            return 'draft'
        
        status_lower = status.lower()
        for mapped_status, keywords in STATUS_MAPPING.items():
            if status_lower in keywords or status_lower == mapped_status:
                return mapped_status
        
        return 'draft'


# ============================================================
# SMART MIGRATION
# ============================================================

class Command(BaseCommand):
    help = 'Import WordPress data with smart matching'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Dry run')
        parser.add_argument('--clear-existing', action='store_true', help='Clear existing data')
        parser.add_argument('--limit', type=int, default=0, help='Limit posts')
        parser.add_argument('--match-all', action='store_true', help='Try to match everything possible')
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear_existing = options['clear_existing']
        limit = options['limit']
        match_all = options['match_all']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("🚀 Smart WordPress Migration Tool - Match Everything"))
        self.stdout.write("="*70)
        
        # Parse SQL files
        all_data = []
        for sql_file in SQL_FILES:
            file_path = os.path.join(os.getcwd(), sql_file)
            if not os.path.exists(file_path):
                continue
            
            raw_data = parse_sql_dump(file_path)
            if raw_data and any(len(v) > 0 for v in raw_data.values()):
                wp_data = WordPressData(raw_data, sql_file)
                all_data.append(wp_data)
        
        if not all_data:
            self.stdout.write(self.style.ERROR("❌ No data found"))
            return
        
        self.print_summary(all_data)
        
        if dry_run:
            return
        
        if clear_existing:
            self.clear_all_data()
        
        self.stdout.write("\n" + self.style.SUCCESS("📥 Smart importing..."))
        
        with transaction.atomic():
            self.smart_migrate(all_data, limit, match_all)
        
        self.stdout.write("\n" + self.style.SUCCESS("🎉 Import completed!"))
    
    def clear_all_data(self):
        """مسح كل البيانات"""
        self.stdout.write("\n🗑️  Clearing data...")
        Comments.objects.all().delete()
        MediaFiles.objects.all().delete()
        Posts.objects.all().delete()
        Tags.objects.all().delete()
        Categories.objects.all().delete()
        Authors.objects.all().delete()
        ContentType.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("✅ Cleared"))
    
    def smart_migrate(self, sites_data, limit, match_all):
        """هجرة ذكية مع محاولة مطابقة كل شيء"""
        
        # ===== 1. Create Content Types =====
        self.stdout.write("\n📦 Creating content types...")
        content_type_map = {}
        
        for ct_key, ct_data in [
            ('infographic', 'إنفوجرافيك', 'Infographic', 'Înfografîk', 1),
            ('video', 'فيديو', 'Video', 'Vîdyo', 2),
            ('documentary', 'وثائقي', 'Documentary', 'Belgesel', 3),
            ('report', 'تقرير', 'Report', 'Rapor', 4),
            ('survey', 'استبيان', 'Survey', 'Anket', 5),
            ('event', 'حدث', 'Event', 'Bûyer', 6),
            ('magazine', 'مجلة', 'Magazine', 'Kovar', 7),
            ('book', 'كتاب', 'Book', 'Pirtûk', 8),
            ('studies', 'دراسات', 'Studies', 'Lêkolîn', 9),
            ('analytics', 'تحليلات', 'Analytics', 'Analîz', 10),
            ('opinion_article', 'مقال رأي', 'Opinion Article', 'Gotara RAY', 11),
            ('files', 'ملفات', 'Files', 'Pel', 12),
        ]:
            ct, created = ContentType.objects.get_or_create(
                name_en=ct_data[2],
                defaults={
                    'name_ar': ct_data[1],
                    'name_ku': ct_data[3],
                    'priority': ct_data[4],
                }
            )
            content_type_map[ct_key] = ct.id
            if created:
                self.stdout.write(f"   ✅ Created: {ct_data[1]}")
        
        default_ct_id = content_type_map['report']
        
        # ===== 2. Smart Users Import =====
        self.stdout.write("\n👤 Smart importing users...")
        author_map = {}
        
        for site in sites_data:
            for uid, user in site.users.items():
                # البحث عن المؤلف بعدة طرق
                author = None
                
                # بالبريد الإلكتروني
                if user['email']:
                    author = Authors.objects.filter(email=user['email']).first()
                
                # بالاسم
                if not author and user['display_name']:
                    author = Authors.objects.filter(full_name=user['display_name']).first()
                
                # بالـ login
                if not author and user['login']:
                    author = Authors.objects.filter(slug=user['login']).first()
                
                if not author:
                    author = Authors.objects.create(
                        full_name=user['display_name'] or user['login'],
                        email=user['email'] if user['email'] else None,
                        slug=user['nicename'] or user['login'],
                    )
                    self.stdout.write(f"   + Created author: {author.full_name}")
                
                author_map[(site.source, uid)] = author.id
        
        self.stdout.write(f"   ✅ Authors: {len(author_map)}")
        
        # ===== 3. Smart Categories Import =====
        self.stdout.write("\n📂 Smart importing categories...")
        cat_map = {}
        
        for site in sites_data:
            for cat in site.categories:
                category = None
                
                # البحث بالـ slug
                if cat['slug']:
                    category = Categories.objects.filter(slug=cat['slug']).first()
                
                # البحث بالاسم
                if not category:
                    for lang in ['name_ar', 'name_ku', 'name_en']:
                        category = Categories.objects.filter(**{lang: cat['name']}).first()
                        if category:
                            break
                
                if not category:
                    # تحديد نوع المحتوى المناسب
                    ct_id = default_ct_id
                    for ct_key, keywords in CONTENT_TYPE_MAPPING.items():
                        for kw in keywords:
                            if kw in cat['name'].lower():
                                ct_id = content_type_map.get(ct_key, default_ct_id)
                                break
                    
                    category = Categories.objects.create(
                        slug=cat['slug'] or self.slugify(cat['name']),
                        name_ar=cat['name'],
                        name_ku=cat['name'],
                        name_en=cat['name'],
                        description=cat['description'][:500] if cat['description'] else None,
                        content_type_id=ct_id,
                    )
                    self.stdout.write(f"   + Created category: {category.name_ar}")
                
                cat_map[(site.source, cat['original_id'])] = category.id
        
        self.stdout.write(f"   ✅ Categories: {len(cat_map)}")
        
        # ===== 4. Smart Tags Import =====
        self.stdout.write("\n🏷️  Smart importing tags...")
        tag_map = {}
        
        for site in sites_data:
            for tag in site.tags:
                existing_tag = None
                
                # البحث بالاسم الكردي أولاً
                existing_tag = Tags.objects.filter(name_ku=tag['name']).first()
                
                if not existing_tag:
                    existing_tag = Tags.objects.filter(name_ar=tag['name']).first()
                
                if not existing_tag:
                    existing_tag = Tags.objects.filter(name_en=tag['name']).first()
                
                if not existing_tag:
                    existing_tag = Tags.objects.filter(slug=self.slugify(tag['name'])).first()
                
                if not existing_tag:
                    existing_tag = Tags.objects.create(
                        name_ar=tag['name'],
                        name_ku=tag['name'],
                        name_en=tag['name'],
                        slug=self.slugify(tag['name']),
                    )
                    self.stdout.write(f"   + Created tag: {existing_tag.name_ar}")
                
                tag_map[(site.source, tag['original_id'])] = existing_tag.id
        
        self.stdout.write(f"   ✅ Tags: {len(tag_map)}")
        
        # ===== 5. Smart Posts Import =====
        self.stdout.write("\n📝 Smart importing posts...")
        posts_count = 0
        skipped = 0
        
        for site in sites_data:
            all_posts = site.posts + site.pages
            if limit > 0:
                all_posts = all_posts[:limit]
            
            for post in tqdm(all_posts, desc="   Importing"):
                author_id = author_map.get((site.source, post['original_author']))
                cat_id = cat_map.get((site.source, post['category_id'])) if post.get('category_id') else None
                
                # تحديد نوع المحتوى (من كشف تلقائي أو من الميتا)
                ct_id = default_ct_id
                if post['detected_content_type']:
                    ct_id = content_type_map.get(post['detected_content_type'], default_ct_id)
                
                # تحديد اللغة
                language = post['detected_language'] or DEFAULT_LANGUAGE
                
                # معالجة التاريخ
                published_at = post['published_at']
                if not published_at:
                    published_at = post['created_at']
                
                # تجنب التكرار
                if Posts.objects.filter(title=post['title']).exists() and match_all:
                    self.stdout.write(f"   ⚠️  Skipping duplicate: {post['title'][:50]}")
                    skipped += 1
                    continue
                
                try:
                    new_post = Posts.objects.create(
                        language=language,
                        title=post['title'][:500],
                        excerpt=post['excerpt'][:500] if post['excerpt'] else None,
                        content=post['content'],
                        content_type_id=ct_id,
                        view_count=post['view_count'],
                        published_at=published_at,
                        is_published=(post['status'] == 'publish'),
                        created_at=post['created_at'],
                        updated_at=post['updated_at'],
                        author_id=author_id,
                        category_id=cat_id,
                    )
                    posts_count += 1
                    
                    # إضافة الوسوم
                    for term_id in post['term_ids']:
                        tag_key = (site.source, term_id)
                        if tag_key in tag_map:
                            new_post.tags.add(tag_map[tag_key])
                    
                except Exception as e:
                    self.stdout.write(f"   ❌ Error: {e}")
                    continue
        
        self.stdout.write(f"\n   ✅ Imported: {posts_count} posts")
        if skipped > 0:
            self.stdout.write(f"   ⚠️  Skipped: {skipped} duplicates")
    
    def slugify(self, text):
        """تحويل النص إلى slug"""
        if not text:
            return None
        from django.utils.text import slugify
        return slugify(text)[:255]
    
    def print_summary(self, sites_data):
        """عرض الملخص"""
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("📊 DATA SUMMARY"))
        self.stdout.write("="*70)
        
        for site in sites_data:
            self.stdout.write(f"\n📁 {os.path.basename(site.source)}")
            self.stdout.write(f"   👤 Users: {len(site.users):,}")
            self.stdout.write(f"   📂 Categories: {len(site.categories):,}")
            self.stdout.write(f"   🏷️  Tags: {len(site.tags):,}")
            self.stdout.write(f"   📝 Posts: {len(site.posts):,}")
            self.stdout.write(f"   📄 Pages: {len(site.pages):,}")
            self.stdout.write(f"   🖼️  Media: {len(site.media_files):,}")
            self.stdout.write(f"   💬 Comments: {len(site.comments):,}")