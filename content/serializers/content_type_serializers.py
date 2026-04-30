# content/serializers/content_type_serializers.py

from rest_framework import serializers
from content.models import ContentType


class ContentTypeSerializer(serializers.ModelSerializer):
    """Serializer لعرض أنواع المحتوى (قائمة مختصرة)"""
    
    class Meta:
        model = ContentType
        fields = ['id', 'name_ar', 'name_ku', 'name_en', 'priority']
        read_only_fields = ['id']


class ContentTypeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء وتحديث أنواع المحتوى"""
    
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