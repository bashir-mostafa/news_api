import os

from django.db import models

class ContentType(models.TextChoices):
    TEXT = 'text'
    INFOGRAPHIC = 'infographic'
    VIDEO = 'video'
    DOCUMENTARY = 'documentary'
    REPORT = 'report'
    SURVEY = 'survey'
    PUBLICATION = 'publication'
    EVENT = 'event'


class Language(models.TextChoices):
    AR = 'ar'
    KU = 'ku'
    EN = 'en'


class PublicationType(models.TextChoices):
    BOOK = 'book'
    MAGAZINE = 'magazine'


class EventType(models.TextChoices):
    DIALOGUE_SESSION = 'dialogue_session'
    FORUM = 'forum'
    MEETING = 'meeting'
    CENTER_NEWS = 'center_news'


class MediaFileType(models.TextChoices):
    IMAGE = 'image'
    VIDEO = 'video'
    PDF = 'pdf'
    AUDIO = 'audio'


class Tags(models.Model):
    name_ar = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="الاسم (عربي)",
    )
    name_ku = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="الاسم (كردي)",
    )
    name_en = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="الاسم (إنجليزي)",
    )
    slug = models.SlugField(
        max_length=255, 
        unique=False,
        null=True,
        blank=True,
        verbose_name="الرابط المختصر",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
        db_column='created_at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ آخر تعديل",
        db_column='updated_at'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ الحذف",
    )


class Authors(models.Model):
    full_name = models.CharField(
        max_length=255,
        verbose_name="الاسم الكامل",
    )
    slug = models.SlugField(
        max_length=255, 
        verbose_name="الرابط المختصر",
        unique=False,
        null=True,
        blank=True,
    )
    bio = models.TextField(
        null=True,
        blank=True,
        verbose_name="السيرة الذاتية",
    )
    profile_image = models.ImageField( 
        upload_to='authors/%Y/%m/%d/',  
        null=True,
        blank=True,
        verbose_name="صورة الملف الشخصي",
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="البريد الإلكتروني",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التعديل",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True, 
        verbose_name="تاريخ الحذف",
    )
    

class Categories(models.Model):
    slug = models.SlugField(
        max_length=255,
        verbose_name="الرابط المختصر",
        unique=False,
        null=True,
        blank=True,
    )
    name_ar = models.CharField(
        max_length=255,
        verbose_name="الاسم (عربي)",
    )
    name_ku = models.CharField(
        max_length=255,
        verbose_name="الاسم (كردي)",
    )
    name_en = models.CharField(
        max_length=255,
        verbose_name="الاسم (إنجليزي)",
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="الوصف",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التعديل",
    )
    deleted_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="تاريخ الحذف",
    )
    class Meta:
        verbose_name = "الوسوم"
        verbose_name_plural = "الوسوم"

    def get_name(self, language='ar'):
        names = {
            'ar': self.name_ar,
            'ku': self.name_ku,
            'en': self.name_en
        }
        return names.get(language, self.name_ar)
    
class Posts(models.Model):
    original_post = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='translations',
        verbose_name="المقال الأصلي",
        help_text="المرجع للمقال الأصلي في حالة الترجمات"
    )
    
    author = models.ForeignKey(
        'Authors',
        on_delete=models.SET_NULL,
        unique=False,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name="الكاتب",
        db_column='author_id'
    )
    
    category = models.ForeignKey(
        'Categories',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name="التصنيف",
        db_column='category_id'
    )
    
    tags = models.ManyToManyField(
        'Tags',
        blank=True,
        related_name='posts',
        verbose_name="الوسوم"
    )
    
    language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.AR,
        verbose_name="اللغة",
        db_index=True,
        help_text="لغة المحتوى"
    )
    
    title = models.CharField(
        max_length=500,
        verbose_name="العنوان",
        db_index=True,
        help_text="عنوان المقال حسب اللغة المختارة"
    )
    
    excerpt = models.TextField(
        null=True,
        blank=True,
        verbose_name="الملخص",
        help_text="ملخص قصير للمقال"
    )
    
    content = models.TextField(
        verbose_name="المحتوى",
        help_text="المحتوى الرئيسي للمقال"
    )
    
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices,
        default=ContentType.TEXT,
        verbose_name="نوع المحتوى",
        db_index=True
    )
    
    meta_title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="العنوان التعريفي",
        help_text="عنوان SEO مختلف عن العنوان الرئيسي"
    )
    
    meta_description = models.TextField(
        null=True,
        blank=True,
        verbose_name="الوصف التعريفي",
        help_text="وصف SEO لمحركات البحث"
    )
    
    featured_image = models.ImageField(
        upload_to='posts/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name="الصورة المميزة",
        help_text="الصورة المميزة للمقال"
    )
    
    view_count = models.IntegerField(
        default=0,
        verbose_name="عدد المشاهدات",
        db_index=True
    )
    
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ النشر",
        db_index=True
    )
    
    is_published = models.BooleanField(
        default=False,
        verbose_name="منشور",
        db_index=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التعديل",
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ الحذف",
    )

class Comments(models.Model):
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=255, verbose_name="الاسم")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    comment = models.TextField(verbose_name="التعليق")
    is_approved = models.BooleanField(default=True, verbose_name="موافق عليه")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")
    class Meta:
        db_table = 'content_comments'
        verbose_name = "تعليق"
        verbose_name_plural = "التعليقات"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"

class Surveys(models.Model):
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='surveys')
    question = models.CharField(max_length=255, verbose_name="السؤال")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    closes_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الإغلاق")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")
    class Meta:
        db_table = 'content_surveys'
        verbose_name = "استبيان"
        verbose_name_plural = "الاستبيانات"
        ordering = ['-created_at']

    def __str__(self):
        return f"Survey for {self.post.title}: {self.question}"
    
class SurveyOptions(models.Model):
    survey = models.ForeignKey(Surveys, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255, verbose_name="نص الخيار")
    vote_count = models.IntegerField(default=0, verbose_name="عدد الأصوات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")
    class Meta:
        db_table = 'content_survey_options'
        verbose_name = "خيار استبيان"
        verbose_name_plural = "خيارات الاستبيان"
        ordering = ['-created_at']

    def __str__(self):
        return f"Option for {self.survey.post.title}: {self.option_text}"
    

class Events(models.Model):
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(
            max_length=50, 
            choices=EventType.choices,  
            default=EventType.MEETING,
            verbose_name="نوع الحدث"
        )
    event_date = models.DateTimeField(verbose_name="تاريخ الحدث")
    location = models.CharField(max_length=255, verbose_name="الموقع")
    attendees_count = models.IntegerField(default=0, verbose_name="عدد الحضور")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")
    class Meta:
        db_table = 'content_events'
        verbose_name = "حدث"
        verbose_name_plural = "الأحداث"
        ordering = ['-created_at']
    def __str__(self):
        return f"Event for {self.post.title}: {self.event_type} on {self.event_date}"
    

class Publications(models.Model):
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='publications')
    publication_type = models.CharField(
            max_length=50, 
            choices=PublicationType.choices,  
            default=PublicationType.BOOK,
            verbose_name="نوع النشر")
    issue_number = models.CharField(max_length=50, verbose_name="رقم الإصدار")
    volume = models.CharField(max_length=50, verbose_name="المجلد")
    isbn = models.CharField(max_length=20, verbose_name="رقم ISBN")
    download_url = models.URLField(null=True, blank=True, verbose_name="رابط التحميل")
    cover_image = models.ImageField(upload_to='publications/%Y/%m/%d/', null=True, blank=True, verbose_name="صورة الغلاف")
    page_count = models.IntegerField(null=True, blank=True, verbose_name="عدد الصفحات")
    publish_year = models.IntegerField(null=True, blank=True, verbose_name="سنة النشر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")
    class Meta:
        db_table = 'content_publications'
        verbose_name = "نشر"
        verbose_name_plural = "النشرات"
        ordering = ['-created_at']
    def __str__(self):
        return f"Publication for {self.post.title}: {self.publication_type} - Issue {self.issue_number}"
    

class MediaFiles(models.Model):
    post = models.ForeignKey(
        Posts, 
        on_delete=models.CASCADE, 
        related_name='media_files',
        verbose_name="المقال"
    )
    
    file_type = models.CharField(
        max_length=20, 
        choices=MediaFileType.choices,  
        verbose_name="نوع الملف"
    )
    
    src = models.FileField(
        upload_to='media_files/%Y/%m/%d/',
        null=True, 
        blank=True, 
        verbose_name="الملف"
    )

    external_url = models.URLField(
        null=True, blank=True,
        verbose_name="رابط خارجي"
    )
    
    alt_text = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="النص البديل"
    )
    
    caption = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="الشرح"
    )
    
    mime_type = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="نوع MIME"
    )
    
    file_size_kb = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="حجم الملف (KB)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")
    
    class Meta:
        db_table = 'content_media_files'
        verbose_name = "ملف وسائط"
        verbose_name_plural = "ملفات الوسائط"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Media file for {self.post.title}: {self.file_type}"
    def delete_physical_file(self):
        if self.src and not self.external_url:
            try:
                if os.path.isfile(self.src.path):
                    os.remove(self.src.path)
                    return True, "File deleted successfully"
                else:
                    return False, "File not found on disk"
            except Exception as e:
                return False, str(e)
        return True, "No physical file to delete (external URL)"
    
    def hard_delete(self):
        self.delete_physical_file()
        self.delete()
    def get_url(self):
        if self.src:
            return self.src.url
        return None
