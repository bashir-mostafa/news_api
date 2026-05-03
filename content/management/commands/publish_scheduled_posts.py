# content/management/commands/publish_scheduled_posts.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from content.models import Posts

class Command(BaseCommand):
    help = 'Publish scheduled posts whose published_at has arrived'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be published without actually publishing',
        )
    
    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options.get('dry_run', False)
        
        scheduled_posts = Posts.objects.filter(
            is_published=False,
            published_at__isnull=False,
            published_at__lte=now,
            deleted_at__isnull=True
        )
        
        count = scheduled_posts.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No scheduled posts to publish'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Found {count} scheduled post(s) ==='))
        
        for post in scheduled_posts:
            self.stdout.write(f'{post.title} (ID: {post.id}) - scheduled for {post.published_at}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDry run mode - no changes made'))
            return
        
        published_count = 0
        for post in scheduled_posts:
            post.is_published = True
            post.save()
            self.stdout.write(self.style.SUCCESS(f'Published: {post.title} (ID: {post.id})'))
            published_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully published {published_count} scheduled post(s)'))