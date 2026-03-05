from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from ..models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="كلمة المرور"
    )
    created_by_username = serializers.StringRelatedField(
        source='created_by',
        read_only=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'password', 'full_name', 'role',
            'is_active', 'created_at', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'created_by_username']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'full_name': {'required': True}
            
        }

    def validate_username(self, value):
        
        if not value or value.strip() == '':
            raise serializers.ValidationError("the username is required")
        
        if self.instance and self.instance.username == value:
            return value
        
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("the username is already exists")
        
        return value

    def validate_email(self, value):
        """
        التحقق من البريد الإلكتروني
        """
        if not value or value.strip() == '':
            raise serializers.ValidationError("the email is required")
        
        if self.instance and self.instance.email == value:
            return value
        
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("the email is already exists")
        
        return value

    def validate_password(self, value):
        """
        التحقق من كلمة المرور
        """
        if not value:
            raise serializers.ValidationError("the password is required")
        
        if len(value) < 8:
            raise serializers.ValidationError("the password must be at least 8 characters long")
        
        return value

    def validate_full_name(self, value):
        """
        التحقق من الاسم الكامل (اختياري)
        """
        if value and len(value) < 3:
            raise serializers.ValidationError("the full name must be at least 3 characters long")
        return value

    def validate(self, data):
        """
        تحقق إضافي على مستوى الكائن
        """
        if self.instance is None and 'password' and 'username' and 'email' not in data:
            raise serializers.ValidationError("كلمة المرور مطلوبة عند إنشاء مستخدم جديد")
        return data

    def create(self, validated_data):
      
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)  
        user.save()
        return user

    def update(self, instance, validated_data):
       
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):

    created_by_username = serializers.StringRelatedField(source='created_by', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'full_name', 'role', 'role_display',
            'is_active', 'created_at', 'created_by_username'
        ]
        read_only_fields = fields