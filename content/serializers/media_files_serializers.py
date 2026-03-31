# content/serializers/media_files_serializers.py
from rest_framework import serializers
from content.models import MediaFiles, Posts, MediaFileType
import os

class MediaFilesSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    image_file_url = serializers.SerializerMethodField()
    audio_file_url = serializers.SerializerMethodField()
    document_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFiles
        fields = [
            'id',
            'post',
            'post_title',
            'file_type',
            'file_type_display',
            'image_file',
            'image_file_url',
            'video_url',
            'audio_file',
            'audio_file_url',
            'document_file',
            'document_file_url',
            'alt_text',
            'caption',
            'mime_type',
            'file_size_kb',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'mime_type', 'file_size_kb', 'created_at', 'updated_at']
    
    def get_image_file_url(self, obj):
        """إرجاع الرابط الكامل لملف الصورة"""
        if obj.image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_file.url)
            return obj.image_file.url
        return None
    
    def get_audio_file_url(self, obj):
        """إرجاع الرابط الكامل لملف الصوت"""
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None
    
    def get_document_file_url(self, obj):
        """إرجاع الرابط الكامل لملف المستند"""
        if obj.document_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document_file.url)
            return obj.document_file.url
        return None


class MediaFilesCreateUpdateSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Upload image file"
    )
    audio_file = serializers.FileField(
        required=False,
        allow_null=True,
        help_text="Upload audio file"
    )
    document_file = serializers.FileField(
        required=False,
        allow_null=True,
        help_text="Upload document file"
    )
    
    class Meta:
        model = MediaFiles
        fields = [
            'post',
            'file_type',
            'image_file',
            'video_url',
            'audio_file',
            'document_file',
            'alt_text',
            'caption'
        ]
        extra_kwargs = {
            'post': {'required': True, 'error_messages': {'required': 'Post is required'}},
            'file_type': {'required': True, 'error_messages': {'required': 'File type is required'}},
            'image_file': {'required': False, 'allow_null': True},
            'video_url': {'required': False, 'allow_null': True, 'allow_blank': True},
            'audio_file': {'required': False, 'allow_null': True},
            'document_file': {'required': False, 'allow_null': True},
            'alt_text': {'required': False, 'allow_null': True, 'allow_blank': True},
            'caption': {'required': False, 'allow_null': True, 'allow_blank': True},
        }
    
    def validate_file_type(self, value):
        """التحقق من صحة نوع الملف"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("File type is required")
        
        valid_types = [choice[0] for choice in MediaFileType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid file type. Choices: {', '.join(valid_types)}")
        
        return value
    
    def validate_video_url(self, value):
        """التحقق من صحة رابط الفيديو"""
        if value and value.strip():
            if not (value.startswith('http://') or value.startswith('https://')):
                raise serializers.ValidationError("Video URL must start with http:// or https://")
            
            # التحقق من روابط YouTube أو Vimeo (اختياري)
            youtube_patterns = ['youtube.com', 'youtu.be', 'vimeo.com']
            if not any(pattern in value.lower() for pattern in youtube_patterns):
                # هذا مجرد تحذير، يمكنك جعله خطأ إذا أردت
                pass
        return value
    
    def validate_post(self, value):
        if not value:
            raise serializers.ValidationError("Post is required")
        
        if not Posts.objects.filter(id=value.id, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Post does not exist or has been deleted")
        
        return value
    
    def validate(self, data):
        """التحقق من أن الملف المناسب موجود حسب نوع الملف"""
        if self.instance is None:
            required_fields = ['post', 'file_type']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})
        
        file_type = data.get('file_type')
        image_file = data.get('image_file')
        video_url = data.get('video_url')
        audio_file = data.get('audio_file')
        document_file = data.get('document_file')
        
        # التحقق من وجود الملف المناسب حسب النوع
        if file_type == MediaFileType.IMAGE:
            if not image_file:
                raise serializers.ValidationError({
                    'image_file': 'Image file is required for image type'
                })
        elif file_type == MediaFileType.VIDEO:
            if not video_url:
                raise serializers.ValidationError({
                    'video_url': 'Video URL is required for video type'
                })
        elif file_type == MediaFileType.AUDIO:
            if not audio_file:
                raise serializers.ValidationError({
                    'audio_file': 'Audio file is required for audio type'
                })
        elif file_type == MediaFileType.DOCUMENT:
            if not document_file:
                raise serializers.ValidationError({
                    'document_file': 'Document file is required for document type'
                })
        
        return data
    
    def _get_mime_type(self, file_obj):
        """استخراج نوع MIME من الملف"""
        if file_obj:
            import magic
            try:
                return magic.from_buffer(file_obj.read(1024), mime=True)
            except:
                return None
        return None
    
    def _get_file_size_kb(self, file_obj):
        """استخراج حجم الملف بالكيلوبايت"""
        if file_obj:
            try:
                return file_obj.size // 1024
            except:
                return None
        return None
    
    def create(self, validated_data):
        # استخراج الملفات
        image_file = validated_data.get('image_file')
        audio_file = validated_data.get('audio_file')
        document_file = validated_data.get('document_file')
        
        # تعيين MIME type وحجم الملف
        if image_file:
            validated_data['mime_type'] = self._get_mime_type(image_file) or 'image/*'
            validated_data['file_size_kb'] = self._get_file_size_kb(image_file)
        elif audio_file:
            validated_data['mime_type'] = self._get_mime_type(audio_file) or 'audio/*'
            validated_data['file_size_kb'] = self._get_file_size_kb(audio_file)
        elif document_file:
            validated_data['mime_type'] = self._get_mime_type(document_file) or 'application/*'
            validated_data['file_size_kb'] = self._get_file_size_kb(document_file)
        
        media_file = MediaFiles.objects.create(**validated_data)
        return media_file
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # تحديث MIME type وحجم الملف إذا تم تحديث الملفات
        if 'image_file' in validated_data and validated_data['image_file']:
            instance.mime_type = self._get_mime_type(validated_data['image_file']) or 'image/*'
            instance.file_size_kb = self._get_file_size_kb(validated_data['image_file'])
        elif 'audio_file' in validated_data and validated_data['audio_file']:
            instance.mime_type = self._get_mime_type(validated_data['audio_file']) or 'audio/*'
            instance.file_size_kb = self._get_file_size_kb(validated_data['audio_file'])
        elif 'document_file' in validated_data and validated_data['document_file']:
            instance.mime_type = self._get_mime_type(validated_data['document_file']) or 'application/*'
            instance.file_size_kb = self._get_file_size_kb(validated_data['document_file'])
        
        instance.save()
        return instance


class MediaFilesDetailSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_slug = serializers.CharField(source='post.slug', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    image_file_url = serializers.SerializerMethodField()
    audio_file_url = serializers.SerializerMethodField()
    document_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFiles
        fields = '__all__'
        read_only_fields = ['id', 'mime_type', 'file_size_kb', 'created_at', 'updated_at', 'deleted_at']
    
    def get_image_file_url(self, obj):
        if obj.image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_file.url)
            return obj.image_file.url
        return None
    
    def get_audio_file_url(self, obj):
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None
    
    def get_document_file_url(self, obj):
        if obj.document_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document_file.url)
            return obj.document_file.url
        return None


class MediaFilesListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFiles
        fields = [
            'id',
            'post',
            'post_title',
            'file_type',
            'file_type_display',
            'file_url',
            'alt_text',
            'caption',
            'file_size_kb',
            'created_at'
        ]
    
    def get_file_url(self, obj):
        """إرجاع الرابط المناسب حسب نوع الملف"""
        request = self.context.get('request')
        if obj.file_type == MediaFileType.IMAGE and obj.image_file:
            if request:
                return request.build_absolute_uri(obj.image_file.url)
            return obj.image_file.url
        elif obj.file_type == MediaFileType.VIDEO and obj.video_url:
            return obj.video_url
        elif obj.file_type == MediaFileType.AUDIO and obj.audio_file:
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        elif obj.file_type == MediaFileType.DOCUMENT and obj.document_file:
            if request:
                return request.build_absolute_uri(obj.document_file.url)
            return obj.document_file.url
        return None


class MediaFilesDeletedListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    
    class Meta:
        model = MediaFiles
        fields = [
            'id',
            'post',
            'post_title',
            'file_type',
            'file_type_display',
            'alt_text',
            'caption',
            'mime_type',
            'file_size_kb',
            'created_at',
            'deleted_at'
        ]