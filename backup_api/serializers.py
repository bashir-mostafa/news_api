# backup_api/serializers.py
from rest_framework import serializers

class BackupSerializer(serializers.Serializer):
    app_names = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of apps to backup (empty for all)"
    )
    compress = serializers.BooleanField(
        default=True,
        help_text="Compress backup file"
    )
    exclude = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Apps or models to exclude"
    )
    include_media = serializers.BooleanField(
        default=True,
        help_text="Include media files in backup"
    )

class RestoreSerializer(serializers.Serializer):
    backup_file = serializers.CharField(
        required=True,
        help_text="Backup filename to restore"
    )
    include_media = serializers.BooleanField(
        default=True,
        help_text="Restore media files as well"
    )

class ReplaceSerializer(serializers.Serializer):
    backup_file = serializers.CharField(
        required=True,
        help_text="Backup filename to restore"
    )
    include_media = serializers.BooleanField(
        default=True,
        help_text="Restore media files as well"
    )
    confirmation = serializers.BooleanField(
        required=True,
        help_text="Must be true to confirm replace operation"
    )

class BackupFileSerializer(serializers.Serializer):
    filename = serializers.CharField()
    size = serializers.CharField()
    created_at = serializers.DateTimeField()
    file_path = serializers.CharField()
    type = serializers.CharField(required=False)