# content/serializers/content_type_serializers.py

from rest_framework import serializers
from content.models import ContentType, Categories


class ContentTypeSerializer(serializers.ModelSerializer):
    """Serializer لعرض أنواع المحتوى (قائمة مختصرة)"""
    
    categories_count = serializers.SerializerMethodField()
    
    categories_list = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentType
        fields = ['id', 'name_ar', 'name_ku', 'name_en', 'priority', 'created_at', 'updated_at', 'categories_count', 'categories_list']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_categories_count(self, obj):
        """عدد التصنيفات المرتبطة بنوع المحتوى"""
        return obj.categories_set.filter(deleted_at__isnull=True).count()
    
    def get_categories_list(self, obj):
        """قائمة التصنيفات المرتبطة بنوع المحتوى"""
        categories = obj.categories_set.filter(deleted_at__isnull=True)
        return [
            {
                'id': cat.id,
                'name_ar': cat.name_ar,
                'name_ku': cat.name_ku,
                'name_en': cat.name_en,
                'slug': cat.slug,
            }
            for cat in categories
        ]


class ContentTypeDetailSerializer(serializers.ModelSerializer):
    """Serializer لعرض تفاصيل نوع المحتوى (مع كل التصنيفات)"""
    
    categories = serializers.SerializerMethodField()
    categories_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    
    def get_categories(self, obj):
        """جميع التصنيفات المرتبطة بنوع المحتوى"""
        categories = obj.categories_set.filter(deleted_at__isnull=True)
        return [
            {
                'id': cat.id,
                'name_ar': cat.name_ar,
                'name_ku': cat.name_ku,
                'name_en': cat.name_en,
                'slug': cat.slug,
                'posts_count': cat.posts.filter(deleted_at__isnull=True, is_published=True).count(),
                'created_at': cat.created_at,
                'updated_at': cat.updated_at,
            }
            for cat in categories
        ]
    
    def get_categories_count(self, obj):
        """عدد التصنيفات المرتبطة"""
        return obj.categories_set.filter(deleted_at__isnull=True).count()
    
    def get_posts_count(self, obj):
        """عدد المنشورات المرتبطة بنوع المحتوى"""
        return obj.posts.filter(deleted_at__isnull=True, is_published=True).count()


class ContentTypeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء وتحديث أنواع المحتوى"""
    
    class Meta:
        model = ContentType  
        fields = ['id', 'name_ar', 'name_ku', 'name_en', 'priority']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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


# ============ SERIALIZER FOR CATEGORIES WITH CONTENT TYPE ============

class CategoryWithContentTypeSerializer(serializers.ModelSerializer):
    """Serializer لعرض التصنيفات مع معلومات نوع المحتوى"""
    
    content_type_name = serializers.CharField(source='content_type.name_ar', read_only=True)
    content_type_priority = serializers.IntegerField(source='content_type.priority', read_only=True)
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Categories
        fields = [
            'id', 'slug', 'name_ar', 'name_ku', 'name_en',
            'content_type', 'content_type_name', 'content_type_priority',
            'posts_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_posts_count(self, obj):
        """عدد المنشورات في هذا التصنيف"""
        return obj.posts.filter(deleted_at__isnull=True, is_published=True).count()


class ContentTypeWithCategoriesSerializer(ContentTypeSerializer):
    """Serializer لعرض نوع المحتوى مع جميع تصنيفاته"""
    
    categories = serializers.SerializerMethodField()
    
    class Meta(ContentTypeSerializer.Meta):
        fields = ContentTypeSerializer.Meta.fields + ['categories']
    
    def get_categories(self, obj):
        """جلب جميع التصنيفات المرتبطة"""
        categories = obj.categories_set.filter(deleted_at__isnull=True)
        return CategoryWithContentTypeSerializer(categories, many=True).data