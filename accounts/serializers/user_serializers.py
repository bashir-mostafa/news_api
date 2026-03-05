from rest_framework import serializers
from ..models import CustomUser
from rest_framework.exceptions import ValidationError
import re

class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "role",
            "password",
            "password2",
            "created_at",
            "updated_at",
            "created_by",
        )
        read_only_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }
    
    # ========== التحقق من الحقول ==========
    
    def validate_username(self, value):
        """التحقق من اسم المستخدم"""
        if not value:
            raise ValidationError({"detail": "اسم المستخدم مطلوب"})
        
        if len(value) < 3:
            raise ValidationError({"detail": "اسم المستخدم يجب أن يكون 3 أحرف على الأقل"})
        
        # للمستخدم الجديد فقط
        if not self.instance and CustomUser.objects.filter(username=value).exists():
            raise ValidationError({"detail": "اسم المستخدم موجود بالفعل"})
        
        return value
    
    def validate_email(self, value):
        """التحقق من البريد الإلكتروني"""
        if not value:
            raise ValidationError({"detail": "البريد الإلكتروني مطلوب"})
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValidationError({"detail": "البريد الإلكتروني غير صحيح"})
        
        # للمستخدم الجديد فقط
        if not self.instance and CustomUser.objects.filter(email=value).exists():
            raise ValidationError({"detail": "البريد الإلكتروني مستخدم بالفعل"})
        
        return value
    
    def validate_password(self, value):
        """التحقق من كلمة المرور"""
        if value and len(value) < 8:
            raise ValidationError({"detail": "كلمة المرور يجب أن تكون 8 أحرف على الأقل"})
        return value
    
    # ========== التحقق العام ==========
    
    def validate(self, attrs):
        """التحقق من العلاقات بين الحقول"""
        password = attrs.get('password')
        password2 = attrs.pop('password2', None)
        
        # تحقق تطابق كلمة المرور
        if password and password2 and password != password2:
            raise ValidationError({"detail": "كلمة المرور غير متطابقة"})
        
        return attrs
    
    # ========== إنشاء/تحديث ==========
    
    def create(self, validated_data):
        """إنشاء مستخدم جديد"""
        password = validated_data.pop('password', None)
        
        if not password:
            raise ValidationError({"message": "the password is required"})
        
        user = CustomUser.objects.create_user(**validated_data, password=password)
        return user
    
    def update(self, instance, validated_data):
        """تحديث مستخدم"""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "role",
            "created_at",
        )