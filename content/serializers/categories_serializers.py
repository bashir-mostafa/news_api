from rest_framework import serializers
from content.models import Categories, ContentType
from content.serializers.content_type_serializers import ContentTypeSerializer
import re

class CategoriesSerializer(serializers.ModelSerializer):
    """Serializer لعرض التصنيفات (قائمة مختصرة)"""
    content_type_name = serializers.CharField(source='content_type.name_ar', read_only=True)
    
    class Meta:
        model = Categories
        fields = [
            'id',
            'slug',
            'name_ar',
            'name_ku',
            'name_en',
            'content_type',
            'content_type_name',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategoriesCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء وتحديث التصنيفات"""
    
    class Meta:
        model = Categories
        fields = ['slug', 'name_ar', 'name_ku', 'name_en', 'content_type', 'description']
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
        
        if not ContentType.objects.filter(id=value.id, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("نوع المحتوى غير موجود")
        
        return value
    
    def validate_slug(self, value):
        """التحقق من صحة الـ slug (اختياري)"""
        if value:
            # يمكن إضافة تحقق من uniqueness للـ slug
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
        
        # التأكد من أن الـ slug تم إنشاؤه تلقائياً إذا لم يتم توفيره
        if 'slug' not in data or not data.get('slug'):
            # إنشاء slug تلقائي من الاسم العربي
            name_ar = data.get('name_ar', '')
            if name_ar:
                # تنظيف النص العربي للـ slug
                import re
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
    content_type = ContentTypeSerializer(source='content_type', read_only=True)
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Categories
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    
    def get_posts_count(self, obj):
        """عدد المقالات المرتبطة بهذا التصنيف"""
        return obj.posts.filter(deleted_at__isnull=True, is_published=True).count()


class CategoriesListSerializer(serializers.ModelSerializer):
    """Serializer للقائمة المختصرة (للـ dropdown أو الـ select)"""
    content_type_name = serializers.CharField(source='content_type.name_ar', read_only=True)
    
    class Meta:
        model = Categories
        fields = ['id', 'slug', 'name_ar', 'name_ku', 'name_en', 'content_type_name', 'created_at']


class CategoriesByContentTypeSerializer(serializers.ModelSerializer):
    """Serializer للتصنيفات حسب نوع المحتوى"""
    
    class Meta:
        model = Categories
        fields = ['id', 'slug', 'name_ar', 'name_ku', 'name_en']