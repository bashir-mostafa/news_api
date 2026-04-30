# content/serializers/content_type_serializers.py

from rest_framework import serializers
from content.models import ContentType, Categories  
from django.utils import timezone


class ContentTypeSerializer(serializers.ModelSerializer):
    """Serializer لعرض أنواع المحتوى"""
    
    class Meta:
        model = ContentType
        fields = ['id', 'name_ar', 'name_ku', 'name_en', 'priority']
        read_only_fields = ['id']


class ContentTypeCreateUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ContentType  
        fields = ['id', 'name_ar', 'name_ku', 'name_en', 'priority']
    
    def validate_name_ar(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("الاسم بالعربية مطلوب")
        if len(value) < 2:
            raise serializers.ValidationError("الاسم بالعربية يجب أن يكون حرفين على الأقل")
        return value
    
    def validate_name_en(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("الاسم بالإنجليزية مطلوب")
        if len(value) < 2:
            raise serializers.ValidationError("الاسم بالإنجليزية يجب أن يكون حرفين على الأقل")
        return value
    
    def validate_name_ku(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("الاسم بالكردية مطلوب")
        if len(value) < 2:
            raise serializers.ValidationError("الاسم بالكردية يجب أن يكون حرفين على الأقل")
        return value
    
    def validate_priority(self, value):
        if value < 0:
            raise serializers.ValidationError("الأولوية لا يمكن أن تكون أقل من 0")
        
      
        if self.instance is None:  
            if ContentType.objects.filter(priority=value, deleted_at__isnull=True).exists():
                raise serializers.ValidationError(f"الأولوية {value} مستخدمة بالفعل من قبل نوع محتوى آخر")
        else: 
            if ContentType.objects.filter(priority=value, deleted_at__isnull=True).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(f"الأولوية {value} مستخدمة بالفعل من قبل نوع محتوى آخر")
        
        return value


class CategoriesSerializer(serializers.ModelSerializer):
    content_type_name = serializers.CharField(source='content_type.name_ar', read_only=True)
    content_type_priority = serializers.IntegerField(source='content_type.priority', read_only=True)
    
    class Meta:
        model = Categories
        fields = [
            'id', 'slug', 'name_ar', 'name_ku', 'name_en',
            'content_type',  
            'content_type_name',  
            'content_type_priority',  
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategoriesCreateUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Categories
        fields = ['id', 'slug', 'name_ar', 'name_ku', 'name_en', 'content_type'] 
    
    def validate_name_ar(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("الاسم بالعربية مطلوب")
        if len(value) < 2:
            raise serializers.ValidationError("الاسم بالعربية يجب أن يكون حرفين على الأقل")
        return value
    
    def validate_name_en(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("الاسم بالإنجليزية مطلوب")
        if len(value) < 2:
            raise serializers.ValidationError("الاسم بالإنجليزية يجب أن يكون حرفين على الأقل")
        return value
    
    def validate_name_ku(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("الاسم بالكردية مطلوب")
        if len(value) < 2:
            raise serializers.ValidationError("الاسم بالكردية يجب أن يكون حرفين على الأقل")
        return value
    
    def validate_content_type(self, value):  
        if not value:
            raise serializers.ValidationError("نوع المحتوى مطلوب")
        
        if not ContentType.objects.filter(id=value.id, deleted_at__isnull=True).exists(): 
            raise serializers.ValidationError("نوع المحتوى غير موجود")
        
        return value


class CategoriesDetailSerializer(serializers.ModelSerializer):
    """Serializer لعرض تفاصيل التصنيف"""
    content_type_detail = ContentTypeSerializer(source='content_type', read_only=True)  
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Categories
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    
    def get_posts_count(self, obj):
        return obj.posts.filter(deleted_at__isnull=True, is_published=True).count()