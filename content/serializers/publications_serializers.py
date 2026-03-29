# content/serializers/publications_serializers.py
from rest_framework import serializers
from content.models import Publications, Posts, PublicationType
import re

class PublicationsSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    publication_type_display = serializers.CharField(source='get_publication_type_display', read_only=True)
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Publications
        fields = [
            'id',
            'post',
            'post_title',
            'publication_type',
            'publication_type_display',
            'issue_number',
            'volume',
            'isbn',
            'download_url',
            'cover_image',
            'page_count',
            'publish_year',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_cover_image(self, obj):
        """إرجاع الرابط الكامل لصورة الغلاف"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class PublicationsCreateUpdateSerializer(serializers.ModelSerializer):
    cover_image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Upload cover image"
    )
    
    class Meta:
        model = Publications
        fields = [
            'post',
            'publication_type',
            'issue_number',
            'volume',
            'isbn',
            'download_url',
            'cover_image',
            'page_count',
            'publish_year'
        ]
        extra_kwargs = {
            'post': {'required': True, 'error_messages': {'required': 'Post is required'}},
            'publication_type': {'required': True, 'error_messages': {'required': 'Publication type is required'}},
            'issue_number': {'required': True, 'error_messages': {'required': 'Issue number is required'}},
            'volume': {'required': False, 'allow_null': True, 'allow_blank': True},
            'isbn': {'required': False, 'allow_null': True, 'allow_blank': True},
            'download_url': {'required': False, 'allow_null': True, 'allow_blank': True},
            'cover_image': {'required': False, 'allow_null': True},
            'page_count': {'required': False, 'allow_null': True},
            'publish_year': {'required': False, 'allow_null': True},
        }
    
    def validate_publication_type(self, value):
        """التحقق من صحة نوع النشر"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Publication type is required")
        
        # التحقق من أن القيمة موجودة في الاختيارات
        valid_types = [choice[0] for choice in PublicationType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid publication type. Choices: {', '.join(valid_types)}")
        
        return value
    
    def validate_issue_number(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Issue number is required")
        
        if len(value) > 50:
            raise serializers.ValidationError("Issue number cannot exceed 50 characters")
        
        return value
    
    def validate_volume(self, value):
        if value and value.strip():
            if len(value) > 50:
                raise serializers.ValidationError("Volume cannot exceed 50 characters")
        return value
    
    def validate_isbn(self, value):
        if value and value.strip():
            # التحقق من صيغة ISBN (10 أو 13 رقم)
            isbn_clean = value.replace('-', '').replace(' ', '')
            if len(isbn_clean) not in [10, 13]:
                raise serializers.ValidationError("ISBN must be 10 or 13 digits")
            
            if not isbn_clean.isdigit():
                raise serializers.ValidationError("ISBN must contain only digits and hyphens")
        
        return value
    
    def validate_download_url(self, value):
        if value and value.strip():
            if not (value.startswith('http://') or value.startswith('https://')):
                raise serializers.ValidationError("Download URL must start with http:// or https://")
        return value
    
    def validate_page_count(self, value):
        if value is not None:
            if value < 1:
                raise serializers.ValidationError("Page count must be at least 1")
            if value > 10000:
                raise serializers.ValidationError("Page count cannot exceed 10000")
        return value
    
    def validate_publish_year(self, value):
        if value is not None:
            from django.utils import timezone
            current_year = timezone.now().year
            if value < 1900:
                raise serializers.ValidationError("Publish year cannot be before 1900")
            if value > current_year + 5:
                raise serializers.ValidationError(f"Publish year cannot be more than 5 years in the future")
        return value
    
    def validate_post(self, value):
        if not value:
            raise serializers.ValidationError("Post is required")
        
        # التحقق من وجود المقال وعدم حذفه
        if not Posts.objects.filter(id=value.id, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Post does not exist or has been deleted")
        
        return value
    
    def validate(self, data):
        if self.instance is None:
            required_fields = ['post', 'publication_type', 'issue_number']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})
        
        return data
    
    def create(self, validated_data):
        publication = Publications.objects.create(**validated_data)
        return publication
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PublicationsDetailSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_slug = serializers.CharField(source='post.slug', read_only=True)
    publication_type_display = serializers.CharField(source='get_publication_type_display', read_only=True)
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Publications
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    
    def get_cover_image(self, obj):
        """إرجاع الرابط الكامل لصورة الغلاف"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class PublicationsListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    publication_type_display = serializers.CharField(source='get_publication_type_display', read_only=True)
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Publications
        fields = [
            'id',
            'post',
            'post_title',
            'publication_type',
            'publication_type_display',
            'issue_number',
            'volume',
            'isbn',
            'download_url',
            'cover_image',
            'page_count',
            'publish_year',
            'created_at'
        ]
    
    def get_cover_image(self, obj):
        """إرجاع الرابط الكامل لصورة الغلاف"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class PublicationsDeletedListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    publication_type_display = serializers.CharField(source='get_publication_type_display', read_only=True)
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Publications
        fields = [
            'id',
            'post',
            'post_title',
            'publication_type',
            'publication_type_display',
            'issue_number',
            'volume',
            'isbn',
            'download_url',
            'cover_image',
            'page_count',
            'publish_year',
            'created_at',
            'deleted_at'
        ]
    
    def get_cover_image(self, obj):
        """إرجاع الرابط الكامل لصورة الغلاف"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None