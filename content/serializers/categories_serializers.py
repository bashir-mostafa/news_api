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
            required_fields = [ 'name_ar', 'name_ku', 'name_en']
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
        fields = ['id', 'slug', 'name_ar', 'name_ku', 'name_en','created_at']