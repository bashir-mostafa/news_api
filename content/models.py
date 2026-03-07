from django.db import models


class Tags(models.Model):
    name_ar = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="الاسم (عربي)",
        db_column='name_ar'
    )
    name_ku = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="الاسم (كردي)",
        db_column='name_ku'
    )
    name_en = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="الاسم (إنجليزي)",
        db_column='name_en'
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True,
        verbose_name="الرابط المختصر",
        db_column='slug',
        help_text="سيتم إنشاؤه تلقائياً من الاسم الإنجليزي"
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
        db_column='deleted_at'
    )


class Authors(models.Model):
    full_name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="الاسم الكامل",
        db_column='full_name'
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True,
        verbose_name="الرابط المختصر",
        db_column='slug',
        help_text="سيتم إنشاؤه تلقائياً من الاسم الكامل"
    )
    bio = models.TextField(
        null=True,
        blank=True,
        verbose_name="السيرة الذاتية",
        db_column='bio'
    )
    profile_image = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="صورة الملف الشخصي",
        db_column='profile_image'
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="البريد الإلكتروني",
        db_column='email'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
        db_column='created_at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التعديل",
        db_column='updated_at'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True, 
        verbose_name="تاريخ الحذف",
        db_column='deleted_at'
    )

