# content/management/commands/import_wordpress.py
"""
WordPress SQL Importer — نسخة مصلحة
======================================
المشاكل المحلولة:
  الـ Parser الجديد يتتبّع حالة السلاسل، لا يوقف عند ; داخل محتوى المنشور
  دعم multi-row INSERT
  Resume بملف تتبّع خارجي بدون تعديل الموديل
  --reset-tracker لإعادة الاستيراد من الصفر
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from content.models import (
    ContentType, Authors, Categories, Tags, Posts, Comments,
    Language, MediaFiles,
)
import os, re, shutil, json
from datetime import datetime
from pathlib import Path


# ══════════════════════════════════════════════════════════════════
#  SQL PARSER  — يتتبّع حالة السلاسل، لا يوقف عند ; داخل القيم
# ══════════════════════════════════════════════════════════════════

def iter_insert_rows(content: str, table: str):
    header_re = re.compile(
        rf"INSERT\s+INTO\s+`?{re.escape(table)}`?\s",
        re.IGNORECASE,
    )
    content_upper = content.upper()

    for hdr in header_re.finditer(content):
        vpos = content_upper.find("VALUES", hdr.end())
        if vpos == -1:
            continue
        pos = vpos + 6
        while pos < len(content) and content[pos] in " \t\n\r":
            pos += 1

        buf, in_str, esc = [], False, False
        while pos < len(content):
            ch = content[pos]
            if esc:
                buf.append(ch); esc = False
            elif ch == "\\" and in_str:
                buf.append(ch); esc = True
            elif ch == "'" and not in_str:
                in_str = True; buf.append(ch)
            elif ch == "'" and in_str:
                if pos + 1 < len(content) and content[pos + 1] == "'":
                    buf.append("''"); pos += 2; continue
                in_str = False; buf.append(ch)
            elif ch == ";" and not in_str:
                break
            else:
                buf.append(ch)
            pos += 1

        values_block = "".join(buf).strip()
        for row_str in _split_rows(values_block):
            row_str = row_str.strip()
            if row_str.startswith("(") and row_str.endswith(")"):
                row_str = row_str[1:-1]
            yield _parse_values(row_str)


def _split_rows(block: str):
    rows, cur, depth, in_str, esc = [], [], 0, False, False
    for ch in block:
        if esc:
            cur.append(ch); esc = False; continue
        if ch == "\\" and in_str:
            cur.append(ch); esc = True; continue
        if ch == "'" and not in_str:
            in_str = True; cur.append(ch); continue
        if ch == "'" and in_str:
            in_str = False; cur.append(ch); continue
        if in_str:
            cur.append(ch); continue
        if ch == "(":
            depth += 1; cur.append(ch); continue
        if ch == ")":
            depth -= 1
            if depth == 0:
                rows.append("".join(cur) + ")"); cur = []; continue
            cur.append(ch); continue
        cur.append(ch)
    return rows


def _parse_values(row_str: str):
    vals, cur, in_str, esc = [], [], False, False
    for ch in row_str:
        if esc:
            cur.append(ch); esc = False; continue
        if ch == "\\" and in_str:
            cur.append(ch); esc = True; continue
        if ch == "'" and not in_str:
            in_str = True; cur.append(ch); continue
        if ch == "'" and in_str:
            in_str = False; cur.append(ch); continue
        if ch == "," and not in_str:
            vals.append("".join(cur).strip()); cur = []; continue
        cur.append(ch)
    if cur:
        vals.append("".join(cur).strip())
    return [_clean(v) for v in vals]


def _clean(val: str):
    if not val or val.upper() == "NULL":
        return None
    if val.startswith("'") and val.endswith("'"):
        val = val[1:-1]
    return (val
            .replace("\\'", "'").replace('\\"', '"')
            .replace("\\n", "\n").replace("\\r", "\r")
            .replace("\\t", "\t").strip())


def _to_dt(val):
    if not val:
        return None
    try:
        return timezone.make_aware(datetime.strptime(str(val)[:19], "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════
#  COMMAND
# ══════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = "Import WordPress SQL dumps — fixed parser, resumable, full rollback"
    TRACKER_FILE = "wp_import_tracker.json"

    def add_arguments(self, parser):
        parser.add_argument("--sql-files", nargs="+",
            default=["i5218891_wp4.sql", "i5218891_wp9.sql", "i7736595_wp1.sql"])
        parser.add_argument("--clear", action="store_true")
        parser.add_argument("--reset-tracker", action="store_true",
            help="Delete resume tracker and start fresh")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--media-dir", type=str, default="media")
        parser.add_argument("--report", type=str, default="import_report.json")

    def handle(self, *args, **options):
        self._sep()
        self.stdout.write(self.style.SUCCESS("WORDPRESS IMPORT — FIXED PARSER"))
        self._sep()

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY-RUN — nothing will be written"))

        if options["reset_tracker"] or options["clear"]:
            self._delete_tracker()

        raw = self._extract_all(options["sql_files"])

        self.stdout.write(f"\nExtracted:")
        self.stdout.write(f"  posts        : {len(raw['posts'])}")
        self.stdout.write(f"  pages        : {sum(1 for p in raw['posts'] if p['post_type']=='page')}")
        self.stdout.write(f"  users        : {len(raw['users'])}")
        self.stdout.write(f"  terms        : {len(raw['terms'])}")
        self.stdout.write(f"  attachments  : {len(raw['attachments'])}")
        self.stdout.write(f"  post_images  : {len(raw['post_images'])}")
        self.stdout.write(f"  comments     : {len(raw['comments'])}")

        if options["dry_run"]:
            self._save_report(raw, {}, options["report"])
            return

        if options["clear"]:
            self._clear_db()

        stats = {}
        try:
            with transaction.atomic():
                stats = self._load_all(raw, options)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"\nFATAL — full rollback: {exc}"))
            raise

        self._print_final(stats)
        self._save_report(raw, stats, options["report"])

    # ── EXTRACT ────────────────────────────────────────────────

    def _extract_all(self, sql_files):
        raw = {"posts": [], "users": {}, "terms": {},
               "term_taxonomy": {}, "attachments": {},
               "post_images": {}, "term_rels": {}, "comments": []}
        seen_post_ids = set()

        for sql_file in sql_files:
            if not os.path.exists(sql_file):
                self.stdout.write(self.style.WARNING(f"Not found: {sql_file}"))
                continue
            mb = os.path.getsize(sql_file) / 1_048_576
            self.stdout.write(f"\nReading {sql_file}  ({mb:.1f} MB) ...")
            content = Path(sql_file).read_text(encoding="utf-8", errors="ignore")

            before = len(raw["posts"])
            self._parse_posts(content, raw, seen_post_ids)
            self._parse_users(content, raw)
            self._parse_terms(content, raw)
            self._parse_postmeta(content, raw)
            self._parse_term_relationships(content, raw)
            self._parse_comments(content, raw)
            added = len(raw["posts"]) - before
            self.stdout.write(
                f"  +{added} posts/pages | {len(raw['users'])} users | "
                f"{len(raw['terms'])} terms | {len(raw['attachments'])} attachments"
            )

        for tt in raw["term_taxonomy"].values():
            term = raw["terms"].get(tt["term_id"])
            if term:
                tt["name"] = term["name"]
                tt["slug"] = term["slug"]
        return raw

    def _parse_posts(self, content, raw, seen_ids):
        F = dict(id=0, author=1, date=2, content=4, title=5,
                 excerpt=6, status=7, parent=17, guid=18,
                 post_type=20, mime=21)
        for row in iter_insert_rows(content, "wp_posts"):
            if len(row) < 21:
                continue
            g = lambda k: row[F[k]] if len(row) > F[k] else None
            ptype = g("post_type") or "post"
            wp_id = g("id")
            if ptype == "attachment":
                url = g("guid") or ""
                if wp_id and url:
                    raw["attachments"].setdefault(wp_id, {
                        "id": wp_id, "url": url,
                        "mime_type": g("mime"), "parent_post": g("parent"),
                    })
                continue
            if ptype not in ("post", "page"):
                continue
            if not wp_id or wp_id in seen_ids:
                continue
            seen_ids.add(wp_id)
            raw["posts"].append({
                "wp_id": wp_id, "wp_author": g("author"), "date": g("date"),
                "content": g("content") or "", "title": (g("title") or "").strip() or "Untitled",
                "excerpt": g("excerpt") or "", "status": g("status") or "draft",
                "post_type": ptype,
            })

    def _parse_users(self, content, raw):
        for row in iter_insert_rows(content, "wp_users"):
            if len(row) < 2:
                continue
            wp_id = row[0]
            if wp_id and wp_id not in raw["users"]:
                raw["users"][wp_id] = {
                    "wp_id": wp_id, "login": row[1],
                    "email": row[3] if len(row) > 3 else "",
                    "display_name": row[4] if len(row) > 4 else row[1],
                }

    def _parse_terms(self, content, raw):
        for row in iter_insert_rows(content, "wp_terms"):
            if len(row) < 3:
                continue
            tid = row[0]
            if tid and tid not in raw["terms"]:
                raw["terms"][tid] = {"term_id": tid, "name": row[1] or "", "slug": row[2] or ""}
        for row in iter_insert_rows(content, "wp_term_taxonomy"):
            if len(row) < 3:
                continue
            tt_id, term_id, taxonomy = row[0], row[1], row[2]
            if tt_id and taxonomy in ("category", "post_tag"):
                raw["term_taxonomy"].setdefault(tt_id, {
                    "tt_id": tt_id, "term_id": term_id,
                    "taxonomy": taxonomy, "name": "", "slug": "",
                })

    def _parse_postmeta(self, content, raw):
        for row in iter_insert_rows(content, "wp_postmeta"):
            if len(row) < 4:
                continue
            post_id, meta_key, meta_value = row[1], row[2], row[3]
            if meta_key == "_thumbnail_id" and post_id and meta_value:
                raw["post_images"][post_id] = meta_value

    def _parse_term_relationships(self, content, raw):
        for row in iter_insert_rows(content, "wp_term_relationships"):
            if len(row) < 2:
                continue
            post_id, tt_id = row[0], row[1]
            if post_id and tt_id:
                raw["term_rels"].setdefault(post_id, [])
                if tt_id not in raw["term_rels"][post_id]:
                    raw["term_rels"][post_id].append(tt_id)

    def _parse_comments(self, content, raw):
        seen = {c["wp_id"] for c in raw["comments"]}
        for row in iter_insert_rows(content, "wp_comments"):
            if len(row) < 8:
                continue
            cid = row[0]
            if cid and cid not in seen:
                seen.add(cid)
                raw["comments"].append({
                    "wp_id": cid, "wp_post_id": row[1],
                    "author": row[2] or "Anonymous",
                    "email": row[3] if len(row) > 3 else "",
                    "content": row[6] if len(row) > 6 else "",
                    "date": row[7] if len(row) > 7 else None,
                    "approved": (row[11] if len(row) > 11 else "0") == "1",
                })

    # ── LOAD ───────────────────────────────────────────────────

    def _load_all(self, raw, options):
        stats = dict(posts=0, pages=0, skipped=0, authors=0,
                     categories=0, tags=0, images_linked=0, comments=0)

        tracker = self._load_tracker()
        imported_wp_ids      = set(k for k in tracker if not k.startswith("__"))
        imported_comment_ids = set(tracker.get("__comments__", []))

        ct, _ = ContentType.objects.get_or_create(
            name_en="General",
            defaults={"name_ar": "عام", "name_ku": "Gishtî", "priority": 1},
        )
        author_map = self._load_authors(raw["users"], stats)
        cat_map, tag_map = self._load_terms(raw["term_taxonomy"], ct, stats)

        limit = options["limit"]
        posts_raw = raw["posts"][:limit] if limit > 0 else raw["posts"]
        post_map = {}

        for pd in posts_raw:
            wp_id = pd["wp_id"]
            if wp_id in imported_wp_ids:
                django_id = tracker.get(wp_id)
                if django_id:
                    try:
                        post_map[wp_id] = Posts.objects.get(id=django_id)
                    except Posts.DoesNotExist:
                        pass
                stats["skipped"] += 1
                continue

            author = author_map.get(pd["wp_author"]) or Authors.objects.first()
            try:
                post = Posts.objects.create(
                    title=pd["title"][:500],
                    content=pd["content"],
                    excerpt=(pd["excerpt"] or "")[:500] or None,
                    published_at=_to_dt(pd["date"]),
                    is_published=(pd["status"] == "publish"),
                    language=Language.KU,
                    content_type=ct,
                    author=author,
                    view_count=0,
                )
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  Post {wp_id}: {exc}"))
                continue

            post_map[wp_id] = post
            tracker[wp_id] = post.id

            if pd["post_type"] == "page":
                stats["pages"] += 1
            else:
                stats["posts"] += 1

            for tt_id in raw["term_rels"].get(wp_id, []):
                tt = raw["term_taxonomy"].get(tt_id)
                if not tt:
                    continue
                if tt["taxonomy"] == "category" and tt_id in cat_map:
                    post.categories.add(cat_map[tt_id])
                elif tt["taxonomy"] == "post_tag" and tt_id in tag_map:
                    post.tags.add(tag_map[tt_id])

            att_id = raw["post_images"].get(wp_id)
            if att_id and att_id in raw["attachments"]:
                linked = self._link_image(post, raw["attachments"][att_id]["url"], options["media_dir"])
                stats["images_linked"] += linked

            total = stats["posts"] + stats["pages"]
            if total % 100 == 0:
                self.stdout.write(f"  ... {total} imported")
                self._save_tracker(tracker)

        self._save_tracker(tracker)
        self._load_comments(raw["comments"], post_map, imported_comment_ids, tracker, stats)
        return stats

    def _load_authors(self, users, stats):
        author_map = {}
        for wp_id, u in users.items():
            name = (u["display_name"] or u["login"] or "Unknown").strip()[:200]
            slug = slugify(name)[:255] or f"author-{wp_id}"
            author, created = Authors.objects.get_or_create(
                slug=slug, defaults={"full_name": name}
            )
            if created:
                stats["authors"] += 1
            author_map[wp_id] = author
        Authors.objects.get_or_create(slug="default-author", defaults={"full_name": "Default Author"})
        return author_map

    def _load_terms(self, term_taxonomy, ct, stats):
        cat_map, tag_map = {}, {}
        for tt_id, tt in term_taxonomy.items():
            name = (tt["name"] or "").strip()[:200]
            slug = (tt["slug"] or slugify(name) or f"term-{tt_id}")[:255]
            if not name:
                continue
            if tt["taxonomy"] == "category":
                cat, created = Categories.objects.get_or_create(
                    slug=slug,
                    defaults={"name_ar": name, "name_ku": name, "name_en": name, "content_type": ct},
                )
                cat_map[tt_id] = cat
                if created:
                    stats["categories"] += 1
            elif tt["taxonomy"] == "post_tag":
                tag, created = Tags.objects.get_or_create(
                    slug=slug,
                    defaults={"name_ar": name, "name_ku": name, "name_en": name},
                )
                tag_map[tt_id] = tag
                if created:
                    stats["tags"] += 1
        return cat_map, tag_map

    def _link_image(self, post, image_url: str, media_dir: str) -> int:
        filename = os.path.basename(image_url)
        if not filename:
            return 0
        dt = post.published_at or timezone.now()
        year, month, day = str(dt.year), str(dt.month).zfill(2), str(dt.day).zfill(2)
        candidates = [os.path.join(media_dir, filename)]
        for yr in range(2010, 2027):
            for mo in range(1, 13):
                ms = str(mo).zfill(2)
                for base in ("uploads", "posts", "wp-content/uploads"):
                    candidates.append(os.path.join(media_dir, base, str(yr), ms, filename))
        for src in dict.fromkeys(candidates):
            if not os.path.exists(src):
                continue
            try:
                ext = os.path.splitext(filename)[1]
                safe = re.sub(r"[^a-zA-Z0-9]", "_", post.title[:30])
                new_name = f"{year}{month}{day}_{post.id}_{safe}{ext}"
                target = os.path.join(media_dir, "posts", year, month, day)
                os.makedirs(target, exist_ok=True)
                shutil.copy2(src, os.path.join(target, new_name))
                post.featured_image = f"posts/{year}/{month}/{day}/{new_name}"
                post.save(update_fields=["featured_image"])
                return 1
            except Exception as exc:
                self.stdout.write(f"    Image error: {exc}")
                return 0
        return 0

    def _load_comments(self, comments, post_map, imported_comment_ids, tracker, stats):
        self.stdout.write(f"\nFound {len(comments)} comments in SQL ...")
        done = list(imported_comment_ids)
        first_err = False
        for c in comments:
            if c["wp_id"] in imported_comment_ids:
                continue
            post = post_map.get(c["wp_post_id"])
            if not post:
                continue
            try:
                Comments.objects.create(
                    post=post,
                    author_name=(c["author"] or "")[:200],
                    author_email=(c["email"] or "")[:200],
                    content=c["content"] or "",
                    created_at=_to_dt(c["date"]),
                    is_approved=c["approved"],
                )
                done.append(c["wp_id"])
                stats["comments"] += 1
            except Exception as exc:
                if not first_err:
                    self.stdout.write(self.style.WARNING(
                        f"\n  Comments skipped — field mismatch: {exc}\n"
                        f"  Share your Comments model to fix field names."
                    ))
                    first_err = True
        tracker["__comments__"] = done
        self._save_tracker(tracker)
        if stats["comments"] == 0 and comments:
            self.stdout.write("  Comments skipped (fix model fields if needed)")

    # ── Helpers ────────────────────────────────────────────────

    def _load_tracker(self):
        try:
            with open(self.TRACKER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_tracker(self, tracker):
        with open(self.TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(tracker, f, ensure_ascii=False, indent=2)

    def _delete_tracker(self):
        if os.path.exists(self.TRACKER_FILE):
            os.remove(self.TRACKER_FILE)
            self.stdout.write("Tracker file deleted — starting fresh")

    def _clear_db(self):
        self.stdout.write("\nClearing existing data ...")
        for M in [Comments, MediaFiles, Posts, Tags, Categories, Authors, ContentType]:
            M.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("  Done"))

    def _sep(self):
        self.stdout.write("=" * 60)

    def _print_final(self, stats):
        self._sep()
        self.stdout.write(self.style.SUCCESS("IMPORT COMPLETED"))
        self._sep()
        for k, v in stats.items():
            self.stdout.write(f"  {k:<20}: {v}")
        self._sep()

    def _save_report(self, raw, stats, path="import_report.json"):
        report = {
            "generated_at": timezone.now().isoformat(),
            "extracted": {
                "posts": len(raw["posts"]), "users": len(raw["users"]),
                "terms": len(raw["terms"]), "attachments": len(raw["attachments"]),
                "post_images": len(raw["post_images"]), "comments": len(raw["comments"]),
            },
            "imported": stats,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.stdout.write(f"\nReport saved to {path}")
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Report error: {exc}"))