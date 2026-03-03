from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import translation



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs) 
        if not self.user.is_active:
            raise serializers.ValidationError({"detail": "هذا المستخدم غير مفعل"})
        data.update({
            "id": self.user.id,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "phone_number": self.user.phone_number,
            "role": getattr(self.user, "role", "user"),
        })
        return data


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        help_text=("كلمة المرور (لن تظهر عند الاسترجاع)")
    )
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "full_name",
            "email",
            "password",
            "role",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )
        read_only_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        request = self.context.get("request")
        lang = request.GET.get("lang", "ar") if request else "ar"
        translation.activate(lang)

        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)

        if request and request.user.is_authenticated:
            user.created_by = request.user

        user.save()
        return user


    def update(self, instance, validated_data):
        request = self.context.get("request")
        lang = request.GET.get("lang", "ar") if request else "ar"
        translation.activate(lang)

        password = validated_data.pop("password", None)
        allowed_fields = ["full_name", "email", "is_active", "role"]
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        if request and request.user.is_authenticated:
            instance.updated_by = request.user

        instance.save()
        return instance
