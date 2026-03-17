from rest_framework import serializers
from content.models import Categories
import re

class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = [
            'id',
            'slug',
            'name_ar',
            'name_ku',
            'name_en',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        # extra_kwargs = {
        #     'slug': {'required': True, 'error_messages': {'required': 'Slug is required'}},
        #     'name_ar': {'required': True, 'error_messages': {'required': 'Arabic name is required'}},
        #     'name_ku': {'required': True, 'error_messages': {'required': 'Kurdish name is required'}},
        #     'name_en': {'required': True, 'error_messages': {'required': 'English name is required'}},
        #     'description': {'required': False, 'allow_null': True, 'allow_blank': True},
        #     'sort_order': {'required': False, 'default': 0},
        # }


class CategoriesCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['slug', 'name_ar', 'name_ku', 'name_en', 'description']
        # extra_kwargs = {
        #     'slug': {'required': True, 'error_messages': {'required': 'Slug is required'}},
        #     'name_ar': {'required': True, 'error_messages': {'required': 'Arabic name is required'}},
        #     'name_ku': {'required': True, 'error_messages': {'required': 'Kurdish name is required'}},
        #     'name_en': {'required': True, 'error_messages': {'required': 'English name is required'}},
        #     'description': {'required': False, 'allow_null': True, 'allow_blank': True},
        #     'sort_order': {'required': False, 'allow_null': True},
        # }
    
    def validate_slug(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Slug is required")
        
        if not re.match(r'^[a-z0-9_-]+$', value):
            raise serializers.ValidationError("Slug must contain only lowercase letters, numbers, hyphens and underscores")
        
        queryset = Categories.objects.all()
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.filter(slug=value).exists():
            raise serializers.ValidationError("Category with this slug already exists")
        
        return value
    
    def validate_name_ar(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Arabic name is required")
        
        if len(value) < 2:
            raise serializers.ValidationError("Arabic name must be at least 2 characters long")
        
        return value
    
    def validate_name_ku(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Kurdish name is required")
        
        if len(value) < 2:
            raise serializers.ValidationError("Kurdish name must be at least 2 characters long")
        
        return value
    
    def validate_name_en(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("English name is required")
        
        if len(value) < 2:
            raise serializers.ValidationError("English name must be at least 2 characters long")
        
        return value
    
    
    def validate(self, data):
        if self.instance is None:
            required_fields = ['slug', 'name_ar', 'name_ku', 'name_en']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: "This field is required"})
        
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
    class Meta:
        model = Categories
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


class CategoriesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['id', 'slug', 'name_ar', 'name_ku', 'name_en']