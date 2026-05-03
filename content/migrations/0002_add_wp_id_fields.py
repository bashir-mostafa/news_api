# content/migrations/XXXX_add_wp_id_fields.py
"""
أضف هذا الـ migration كرقم تسلسلي بعد آخر migration موجود.
مثال: إذا آخر ملف هو 0005_... → سمّ هذا 0006_add_wp_id_fields.py
ثم حدّث dependencies أدناه ليطابق الرقم الصحيح.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # ← غيّر هذا ليطابق آخر migration موجود في مشروعك
        ("content", "0001_initial"),
    ]

    operations = [
        # حقل WordPress ID في Posts
        migrations.AddField(
            model_name="posts",
            name="wp_id",
            field=models.CharField(
                max_length=50,
                null=True,
                blank=True,
                unique=True,
                db_index=True,
                verbose_name="WordPress Post ID",
                help_text="المعرّف الأصلي من WordPress — للربط والـ resume",
            ),
        ),
        # حقل WordPress ID في Comments
        migrations.AddField(
            model_name="comments",
            name="wp_id",
            field=models.CharField(
                max_length=50,
                null=True,
                blank=True,
                unique=True,
                db_index=True,
                verbose_name="WordPress Comment ID",
            ),
        ),
    ]