from django.db import models
from django.contrib.auth.models import AbstractUser
# ===================================================================
class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'مدير',
    full_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="الاسم بالكامل"
    )
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.ADMIN,
        help_text="نوع المستخدم"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="تاريخ الإنشاء"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="تاريخ آخر تعديل"
    )
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users_created",
        help_text="المستخدم الذي قام بإنشاء هذا الحساب"
    )
    updated_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users_updated",
        help_text="آخر مستخدم قام بتعديل هذا الحساب"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="تاريخ الحذف"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
