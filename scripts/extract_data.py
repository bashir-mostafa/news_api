# scripts/extract_data.py
import re
import os

def extract_wp_posts(filepath):
    """استخراج wp_posts مباشرة من الملف"""
    
    print(f"\n🔍 Extracting from: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # البحث عن wp_posts بطريقة مختلفة
    # أولاً: البحث عن السطر الذي يحتوي على wp_posts
    lines = content.split('\n')
    
    posts_found = []
    in_posts = False
    post_buffer = []
    
    for line in lines:
        if 'INSERT INTO `wp_posts`' in line or 'INSERT INTO wp_posts' in line:
            in_posts = True
            post_buffer = [line]
        elif in_posts:
            post_buffer.append(line)
            if line.rstrip().endswith(';'):
                # نهاية الـ INSERT
                full_insert = ' '.join(post_buffer)
                posts_found.append(full_insert)
                in_posts = False
    
    print(f"   Found {len(posts_found)} INSERT statements for wp_posts")
    
    # استخراج البيانات من أول INSERT
    if posts_found:
        first_insert = posts_found[0]
        print(f"\n   First INSERT (first 500 chars):")
        print(f"   {first_insert[:50000]}...")
        
        # محاولة استخراج أول صف
        values_match = re.search(r'VALUES\s+(.+)', first_insert, re.IGNORECASE | re.DOTALL)
        if values_match:
            values_part = values_match.group(1).rstrip(';')
            print(f"\n   Values part (first 300 chars):")
            print(f"   {values_part[:300]}...")
            
            # استخراج الصفوف
            row_pattern = r'\(([^)]+(?:[^)]*)\)[^)]*)\)'
            rows = re.findall(row_pattern, values_part)
            print(f"\n   Number of rows: {len(rows)}")
            
            if rows:
                first_row = rows[0]
                print(f"\n   First row (first 200 chars):")
                print(f"   {first_row[:200]}...")
                
                # تفكيك أول صف
                values = []
                current = ''
                in_string = False
                escape = False
                
                for char in first_row:
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
                
                print(f"\n   Extracted {len(values)} values from first row")
                print(f"   ID: {values[0] if len(values) > 0 else 'N/A'}")
                print(f"   Title: {values[5] if len(values) > 5 else 'N/A'}")
                print(f"   Type: {values[20] if len(values) > 20 else 'N/A'}")
                print(f"   Status: {values[7] if len(values) > 7 else 'N/A'}")

# تشغيل
extract_wp_posts("i7736595_wp1.sql")