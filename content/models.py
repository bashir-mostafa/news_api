from django.db import models


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
        unique=True,
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