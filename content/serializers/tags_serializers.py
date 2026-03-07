from rest_framework import serializers
from content.models import Tags
from django.utils.text import slugify

class TagsSerializer(serializers.ModelSerializer):
    """
    serializer أساسي للوسوم
    """
    class Meta:
        model = Tags
        fields = [
            'id', 'name_ar', 'name_ku', 'name_en', 
            'slug', 'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'deleted_at']
    
    def validate_name_en(self, value):
        """
        التحقق من أن الاسم الإنجليزي صالح للـ slug
        """
        if value and not slugify(value):
            raise serializers.ValidationError("الاسم الإنجليزي يجب أن يحتوي على أحرف وأرقام فقط")
        return value

class TagsCreateUpdateSerializer(serializers.ModelSerializer):
    """
    serializer لإنشاء وتحديث الوسوم (يسمح بتعديل جميع الحقول)
    """
    class Meta:
        model = Tags
        fields = ['name_ar', 'name_ku', 'name_en']
    
    def validate(self, data):
        """
        التحقق من عدم تكرار الأسماء
        """
        # التحقق من عدم تكرار الاسم العربي
        if Tags.objects.filter(name_ar=data.get('name_ar')).exists():
            raise serializers.ValidationError({"name_ar": "الاسم العربي موجود مسبقاً"})
        
        # التحقق من عدم تكرار الاسم الكردي
        if Tags.objects.filter(name_ku=data.get('name_ku')).exists():
            raise serializers.ValidationError({"name_ku": "الاسم الكردي موجود مسبقاً"})
        
        # التحقق من عدم تكرار الاسم الإنجليزي
        if Tags.objects.filter(name_en=data.get('name_en')).exists():
            raise serializers.ValidationError({"name_en": "الاسم الإنجليزي موجود مسبقاً"})
        
        return data
    
    def create(self, validated_data):
        """
        إنشاء وسام جديد مع إنشاء slug تلقائياً
        """
        # إنشاء slug من الاسم الإنجليزي
        slug = slugify(validated_data['name_en'])
        
        # التأكد من uniqueness للـ slug
        original_slug = slug
        counter = 1
        while Tags.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # إنشاء الوسام
        tag = Tags.objects.create(
            name_ar=validated_data['name_ar'],
            name_ku=validated_data['name_ku'],
            name_en=validated_data['name_en'],
            slug=slug
        )
        return tag

class TagsListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tags
        fields = ['id', 'name_ar', 'name_ku', 'name_en', 'slug']

class TagsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = [
            'id', 'name_ar', 'name_ku', 'name_en', 
            'slug', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']