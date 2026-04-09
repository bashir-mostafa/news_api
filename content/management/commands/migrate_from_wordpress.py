"""
WordPress to Django Migration Command - Extract ALL Data
"""

import os
import re
from datetime import datetime, timezone
from html import unescape
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import IntegrityError
from tqdm import tqdm

from content.models import Authors, Categories, Tags, Posts, Comments

# ============================================================
# SETTINGS
# ============================================================

SQL_FILES = [
    "i5218891_wp4.sql",
    "i5218891_wp9.sql",
    "i7736595_wp1.sql",
]

DEFAULT_LANGUAGE = "ku"
NOW = datetime.now(timezone.utc)

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
# DATA PROCESSING CLASS - EXTRACT EVERYTHING
# ============================================================

class WordPressData:
    def __init__(self, raw_data, source_file):
        self.source = source_file
        self.raw = raw_data
        self.users = {}
        self.categories = []
        self.tags = []
        self.posts = []
        self.pages = []  # NEW: Store pages separately
        self.comments = []
        self.post_terms = defaultdict(set)
        self.post_categories = {}
        
        self._process()
    
    def _process(self):
        print(f"  Processing {os.path.basename(self.source)}...")
        
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
                    }
                except:
                    continue
        print(f"    Users: {len(self.users)}")
        
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
        
        # ===== Posts - EXTRACT EVERYTHING =====
        # Accept ALL post types and ALL statuses
        for row in self.raw.get('wp_posts', []):
            if len(row) < 21:
                continue
            
            try:
                post_id = int(row[0]) if row[0] else 0
                if not post_id:
                    continue
                
                post_type = str(row[20]) if len(row) > 20 else 'post'
                post_status = str(row[7]) if len(row) > 7 else 'publish'
                
                # NEW: Accept ALL post types (post, page, revision, attachment, etc.)
                # NEW: Accept ALL statuses (publish, draft, private, future, inherit, trash, auto-draft)
                
                title = str(row[5] or '').strip()
                # Don't skip if no title - use ID as fallback
                if not title:
                    title = f"Untitled {post_type} (ID: {post_id})"
                
                # Get category
                category_id = self.post_categories.get(post_id)
                
                # Parse dates
                post_date = row[2] if len(row) > 2 and row[2] else None
                post_modified = row[14] if len(row) > 14 and row[14] else None
                
                post_data = {
                    'original_id': post_id,
                    'original_author': int(row[1]) if len(row) > 1 and row[1] else 0,
                    'title': unescape(title),
                    'content': str(row[4] or ''),
                    'excerpt': unescape(str(row[6] or '')).strip() if len(row) > 6 else None,
                    'status': post_status,
                    'post_type': post_type,  # NEW: Store post type
                    'published_at': post_date,
                    'created_at': post_date or NOW,
                    'updated_at': post_modified or NOW,
                    'category_id': category_id,
                    'term_ids': self.post_terms.get(post_id, set()),
                    'view_count': int(row[22]) if len(row) > 22 and row[22] else 0,
                }
                
                # Separate posts and pages
                if post_type == 'page':
                    self.pages.append(post_data)
                else:
                    self.posts.append(post_data)
                    
            except Exception as e:
                continue
        
        print(f"    Posts: {len(self.posts)}")
        print(f"    Pages: {len(self.pages)}")
        
        # ===== Comments =====
        for row in self.raw.get('wp_comments', []):
            if len(row) >= 11:
                try:
                    # Accept ALL comment types
                    self.comments.append({
                        'post_id': int(row[1]) if row[1] else 0,
                        'name': str(row[2] or 'Anonymous').strip(),
                        'email': str(row[3] or '').strip(),
                        'content': str(row[8] or '').strip(),
                        'approved': str(row[10]) == '1' if len(row) > 10 else False,
                        'created_at': row[6] if len(row) > 6 else NOW,
                    })
                except:
                    continue
        
        print(f"    Comments: {len(self.comments)}")


# ============================================================
# DJANGO COMMAND
# ============================================================

class Command(BaseCommand):
    help = 'Import ALL WordPress data to Django'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Dry run without saving')
        parser.add_argument('--clear-existing', action='store_true', help='Clear existing data')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of posts')
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear_existing = options['clear_existing']
        limit = options['limit']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("🚀 WordPress to Django Migration Tool v6.0 - ALL DATA"))
        self.stdout.write("="*70)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  DRY RUN MODE — No data will be saved"))
        
        all_data = []
        
        for sql_file in SQL_FILES:
            file_path = os.path.join(os.getcwd(), sql_file)
            if not os.path.exists(file_path):
                self.stdout.write(self.style.WARNING(f"⚠️  File not found: {sql_file}"))
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
            self.stdout.write("\n" + self.style.WARNING("⚠️  Dry run completed - No data saved"))
            return
        
        if clear_existing:
            self.stdout.write("\n🗑️  Clearing existing data...")
            with transaction.atomic():
                Comments.objects.all().delete()
                Posts.objects.all().delete()
                Tags.objects.all().delete()
                Categories.objects.all().delete()
                Authors.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✅ Existing data cleared"))
        
        self.stdout.write("\n" + self.style.SUCCESS("📥 Starting import..."))
        
        with transaction.atomic():
            self.migrate_data(all_data, limit)
        
        self.stdout.write("\n" + self.style.SUCCESS("🎉 Import completed successfully!"))
    
    def migrate_data(self, sites_data, limit):
        """Import ALL data"""
        
        # Users
        self.stdout.write("\n👤 Importing users...")
        author_map = {}
        for site in sites_data:
            for uid, user in site.users.items():
                try:
                    author, created = Authors.objects.get_or_create(
                        email=user['email'] if user['email'] else None,
                        defaults={
                            'full_name': user['display_name'] or user['login'],
                            'slug': user['nicename'] or user['login']
                        }
                    )
                    author_map[(site.source, uid)] = author.id
                except Exception as e:
                    continue
        self.stdout.write(f"   ✅ {len(author_map)} users")
        
        # Categories
        self.stdout.write("\n📂 Importing categories...")
        cat_map = {}
        for site in sites_data:
            for cat in site.categories:
                try:
                    category, created = Categories.objects.get_or_create(
                        slug=cat['slug'] or f"cat-{cat['original_id']}",
                        defaults={
                            'name_ar': cat['name'][:200],
                            'name_ku': cat['name'][:200],
                            'name_en': cat['name'][:200],
                            'description': cat['description'][:500] if cat['description'] else None,
                        }
                    )
                    cat_map[(site.source, cat['original_id'])] = category.id
                except Exception as e:
                    continue
        self.stdout.write(f"   ✅ {len(cat_map)} categories")
        
        # Tags
        self.stdout.write("\n🏷️  Importing tags...")
        tag_map = {}
        for site in sites_data:
            for tag in site.tags:
                try:
                    new_tag, created = Tags.objects.get_or_create(
                        name_ku=tag['name'][:100],
                        defaults={
                            'name_ar': tag['name'][:100],
                            'name_en': tag['name'][:100],
                        }
                    )
                    tag_map[(site.source, tag['original_id'])] = new_tag.id
                except Exception as e:
                    continue
        self.stdout.write(f"   ✅ {len(tag_map)} tags")
        
        # Posts
        self.stdout.write("\n📝 Importing posts...")
        posts_count = 0
        
        for site in sites_data:
            all_posts = site.posts + site.pages  # Combine posts and pages
            if limit > 0:
                all_posts = all_posts[:limit]
            
            for post in tqdm(all_posts, desc="   Importing posts"):
                author_id = author_map.get((site.source, post['original_author']))
                cat_id = cat_map.get((site.source, post['category_id'])) if post.get('category_id') else None
                
                try:
                    new_post = Posts.objects.create(
                        language=DEFAULT_LANGUAGE,
                        title=post['title'][:500],
                        excerpt=post['excerpt'][:500] if post['excerpt'] else None,
                        content=post['content'],
                        content_type='text',
                        view_count=post['view_count'],
                        published_at=post['published_at'],
                        is_published=(post['status'] == 'publish'),
                        created_at=post['created_at'],
                        updated_at=post['updated_at'],
                        author_id=author_id,
                        category_id=cat_id,
                    )
                    posts_count += 1
                    
                    for term_id in post['term_ids']:
                        tag_key = (site.source, term_id)
                        if tag_key in tag_map:
                            new_post.tags.add(tag_map[tag_key])
                    
                except Exception as e:
                    continue
        
        self.stdout.write(f"   ✅ {posts_count:,} posts/pages imported")
        
        # Comments
        self.stdout.write("\n💬 Importing comments...")
        comments_count = 0
        for site in sites_data:
            for comment in site.comments:
                try:
                    Comments.objects.create(
                        post_id=comment['post_id'],
                        name=comment['name'][:100],
                        email=comment['email'][:100] if comment['email'] else None,
                        comment=comment['content'],
                        is_approved=comment['approved'],
                        created_at=comment['created_at'],
                    )
                    comments_count += 1
                except:
                    continue
        self.stdout.write(f"   ✅ {comments_count:,} comments imported")
    
    def print_summary(self, sites_data):
        """Display summary"""
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("📊 ALL EXTRACTED DATA SUMMARY"))
        self.stdout.write("="*70)
        
        total_posts = 0
        total_pages = 0
        for site in sites_data:
            self.stdout.write(f"\n📁 Source: {os.path.basename(site.source)}")
            self.stdout.write(f"   👤 Users: {len(site.users):,}")
            self.stdout.write(f"   📂 Categories: {len(site.categories):,}")
            self.stdout.write(f"   🏷️  Tags: {len(site.tags):,}")
            self.stdout.write(f"   📝 Posts: {len(site.posts):,}")
            self.stdout.write(f"   📄 Pages: {len(site.pages):,}")
            self.stdout.write(f"   💬 Comments: {len(site.comments):,}")
            total_posts += len(site.posts)
            total_pages += len(site.pages)
        
        self.stdout.write("\n" + "-"*70)
        self.stdout.write(self.style.SUCCESS(f"🏆 TOTAL POSTS: {total_posts:,}"))
        self.stdout.write(self.style.SUCCESS(f"🏆 TOTAL PAGES: {total_pages:,}"))
        self.stdout.write(self.style.SUCCESS(f"🏆 GRAND TOTAL: {total_posts + total_pages:,}"))
        self.stdout.write("="*70)