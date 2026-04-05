# content/serializers/media_files_serializers.py
from rest_framework import serializers
from content.models import MediaFiles, Posts, MediaFileType
import mimetypes

class MediaFilesSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    src_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFiles
        fields = [
            'id',
            'post',
            'post_title',
            'file_type',
            'file_type_display',
            'src',
            'src_url',
            'external_url', 
            'alt_text',
            'caption',
            'mime_type',
            'file_size_kb',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'mime_type', 'file_size_kb', 'created_at', 'updated_at']
    
    def get_src_url(self, obj):
        if obj.external_url:  
            return obj.external_url
        if obj.src: 
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.src.url)
            return obj.src.url
        return None


class MediaFilesCreateUpdateSerializer(serializers.ModelSerializer):
    src = serializers.FileField(
        required=False,
        allow_null=True,
        help_text="Upload file (image, audio, pdf)"
    )
    external_url = serializers.URLField(  
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="External URL (YouTube, Vimeo, etc.)"
    )
    
    class Meta:
        model = MediaFiles
        fields = [
            'post',
            'file_type',
            'src',
            'external_url',  
            'alt_text',
            'caption'
        ]
        extra_kwargs = {
            'post': {'required': True, 'error_messages': {'required': 'Post is required'}},
            'file_type': {'required': True, 'error_messages': {'required': 'File type is required'}},
            'src': {'required': False, 'allow_null': True},
            'external_url': {'required': False, 'allow_null': True, 'allow_blank': True},
            'alt_text': {'required': False, 'allow_null': True, 'allow_blank': True},
            'caption': {'required': False, 'allow_null': True, 'allow_blank': True},
        }
    
    def validate_file_type(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("File type is required")
        
        valid_types = [choice[0] for choice in MediaFileType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid file type. Choices: {', '.join(valid_types)}")
        
        return value
    
    def validate_external_url(self, value):
        if value and value.strip():
            if not (value.startswith('http://') or value.startswith('https://')):
                raise serializers.ValidationError("URL must start with http:// or https://")
        return value
    
    def validate_post(self, value):
        if not value:
            raise serializers.ValidationError("Post is required")
        
        if not Posts.objects.filter(id=value.id, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Post does not exist or has been deleted")
        
        return value
    
    def validate(self, data):
        """التحقق من أن src أو external_url موجود"""
        if self.instance is None:
            required_fields = ['post', 'file_type']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})
        
        src = data.get('src')
        external_url = data.get('external_url')
        
        if not src and not external_url:
            raise serializers.ValidationError({
                'src': 'Either file or external URL is required'
            })
        
        return data
    
    def _get_mime_type(self, file_obj):
        if file_obj:
            mime_type, _ = mimetypes.guess_type(file_obj.name)
            return mime_type or 'application/octet-stream'
        return None
    
    def _get_file_size_kb(self, file_obj):
        if file_obj:
            try:
                return file_obj.size // 1024
            except:
                return None
        return None
    
    def create(self, validated_data):
        src = validated_data.get('src')
        
        if src:
            validated_data['mime_type'] = self._get_mime_type(src)
            validated_data['file_size_kb'] = self._get_file_size_kb(src)
        
        media_file = MediaFiles.objects.create(**validated_data)
        return media_file
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if 'src' in validated_data and validated_data['src']:
            instance.mime_type = self._get_mime_type(validated_data['src'])
            instance.file_size_kb = self._get_file_size_kb(validated_data['src'])
        
        instance.save()
        return instance


class MediaFilesDetailSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_slug = serializers.CharField(source='post.slug', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    src_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFiles
        fields = '__all__'
        read_only_fields = ['id', 'mime_type', 'file_size_kb', 'created_at', 'updated_at', 'deleted_at']
    
    def get_src_url(self, obj):
        if obj.external_url:
            return obj.external_url
        if obj.src:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.src.url)
            return obj.src.url
        return None


class MediaFilesListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    src_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFiles
        fields = [
            'id',
            'post',
            'post_title',
            'file_type',
            'file_type_display',
            'src_url',
            'external_url',
            'src',
            'alt_text',
            'caption',
            'file_size_kb',
            'created_at'
        ]
    
    def get_src_url(self, obj):
        if obj.external_url:
            return obj.external_url
        if obj.src:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.src.url)
            return obj.src.url
        return None


class MediaFilesDeletedListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    src_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFiles
        fields = [
            'id',
            'post',
            'post_title',
            'file_type',
            'file_type_display',
            'src_url',
            'alt_text',
            'caption',
            'mime_type',
            'file_size_kb',
            'created_at',
            'deleted_at'
        ]
    
    def get_src_url(self, obj):
        if obj.external_url:
            return obj.external_url
        if obj.src:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.src.url)
            return obj.src.url
        return None