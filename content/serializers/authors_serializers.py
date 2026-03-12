from rest_framework import serializers
from content.models import Authors
import re

class AuthorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authors
        fields = [
            'id',
            'full_name',
            'slug',
            'bio',
            'profile_image',
            'email',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AuthorsCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authors
        fields = ['full_name', 'slug', 'bio', 'profile_image', 'email']
        extra_kwargs = {
            'full_name': {'required': True, 'error_messages': {'required': 'Full name is required'}},
            'slug': {'required': True, 'error_messages': {'required': 'Slug is required'}},
            'bio': {'required': False, 'allow_null': True, 'allow_blank': True},
            'profile_image': {'required': False, 'allow_null': True, 'allow_blank': True},
            'email': {'required': False, 'allow_null': True, 'allow_blank': True},
        }
    
    def validate_full_name(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Full name is required")
        
        if len(value) < 3:
            raise serializers.ValidationError("Full name must be at least 3 characters long")
        
        if self.instance and self.instance.full_name == value:
            return value
        
        if Authors.objects.filter(full_name=value).exists():
            raise serializers.ValidationError("Full name already exists")
        
        return value
    
    def validate_slug(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Slug is required")
        
        if not re.match(r'^[a-z0-9_-]+$', value):
            raise serializers.ValidationError("Slug must contain only lowercase letters, numbers, hyphens and underscores")
        
        if self.instance and self.instance.slug == value:
            return value
        
        if Authors.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Slug already exists")
        
        return value
    
    def validate_email(self, value):
        if value and value.strip() != '':
            # تحقق بسيط من صحة الإيميل
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise serializers.ValidationError("Enter a valid email address")
            
            if self.instance and self.instance.email == value:
                return value
            
            if Authors.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already exists")
        
        return value
    
    def validate(self, data):
        if self.instance is None:
            required_fields = ['full_name', 'slug']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: "This field is required"})
        
        return data
    
    def create(self, validated_data):
        author = Authors.objects.create(**validated_data)
        return author
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AuthorsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authors
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


class AuthorsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authors
        fields = ['id', 'full_name', 'slug', 'profile_image', 'email']