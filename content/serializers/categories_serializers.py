# content/serializers/categories_serializers.py

from rest_framework import serializers
from content.models import Categories, ContentType
from .content_type_serializers import ContentTypeSerializer
import re


class CategoriesSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(read_only=True)
    
    class Meta:
        model = Categories
        fields = [
            'id',
            'slug',
            'name_ar',
            'name_ku',
            'name_en',
            'content_type',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategoriesCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء وتحديث التصنيفات"""
    
    class Meta:
        model = Categories
        fields = ['slug', 'name_ar', 'name_ku', 'name_en', 'content_type']
        extra_kwargs = {
            'content_type': {'required': True, 'error_messages': {'required': 'Content type is required'}},
            'description': {'required': False, 'allow_null': True, 'allow_blank': True},
        }
    
    def validate_name_ar(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("الاسم بالعربية مطلوب")
        if len(value) < 2:
            raise serializers.ValidationError("الاسم بالعربية يجب أن يكون حرفين على الأقل")
        return value
    
    def validate_name_ku(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("الاسم بالكردية مطلوب")
        if len(value) < 2:
            raise serializers.ValidationError("الاسم بالكردية يجب أن يكون حرفين على الأقل")
        return value
    
    def validate_name_en(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("الاسم بالإنجليزية مطلوب")
        if len(value) < 2:
            raise serializers.ValidationError("الاسم بالإنجليزية يجب أن يكون حرفين على الأقل")
        return value
    
    def validate_content_type(self, value):
        """التحقق من صحة نوع المحتوى"""
        if not value:
            raise serializers.ValidationError("نوع المحتوى مطلوب")
        
        if isinstance(value, int):
            if not ContentType.objects.filter(id=value, deleted_at__isnull=True).exists():
                raise serializers.ValidationError("نوع المحتوى غير موجود")
        else:
            if not ContentType.objects.filter(id=value.id, deleted_at__isnull=True).exists():
                raise serializers.ValidationError("نوع المحتوى غير موجود")
        
        return value
    
    def validate_slug(self, value):
        """التحقق من صحة الـ slug"""
        if value:
            if self.instance is None:
                if Categories.objects.filter(slug=value, deleted_at__isnull=True).exists():
                    raise serializers.ValidationError("هذا الرابط مستخدم بالفعل")
            else:
                if Categories.objects.filter(slug=value, deleted_at__isnull=True).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError("هذا الرابط مستخدم بالفعل")
        return value
    
    def validate(self, data):
        """تحقق عام على البيانات"""
        if self.instance is None:
            required_fields = ['name_ar', 'name_ku', 'name_en', 'content_type']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"{field} is required"})
        
        if 'slug' not in data or not data.get('slug'):
            name_ar = data.get('name_ar', '')
            if name_ar:
                from django.utils.text import slugify
                slug_base = re.sub(r'[^\w\s]', '', name_ar)
                data['slug'] = slugify(slug_base)[:50]
        
        return data
    
    def create(self, validated_data):
        category = Categories.objects.create(**validated_data)
        return category
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CategoriesDetailSerializer(serializers.ModelSerializer):
    """Serializer لعرض تفاصيل التصنيف (كامل)"""
    content_type = ContentTypeSerializer()
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Categories
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    
    def get_posts_count(self, obj):
        """عدد المقالات المرتبطة بهذا التصنيف"""
        return obj.posts.filter(deleted_at__isnull=True, is_published=True).count()


class CategoriesListSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(read_only=True)
    
    class Meta:
        model = Categories
        fields = [
            'id', 
            'slug', 
            'name_ar', 
            'name_ku', 
            'name_en', 
            'content_type',
            'created_at'
        ]


class CategoriesByContentTypeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Categories
        fields = ['id', 'slug', 'name_ar', 'name_ku', 'name_en']


class CategoriesSelectSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Categories
        fields = ['id', 'display_name']
    
    def get_display_name(self, obj):
        request = self.context.get('request')
        if request:
            language = request.query_params.get('lang', 'ar')
            if language == 'ku':
                return obj.name_ku
            elif language == 'en':
                return obj.name_en
        return obj.name_ar