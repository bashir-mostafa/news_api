from rest_framework import serializers
from ..models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "role",
            "password",
            "created_at",
            "updated_at",
            "created_by",
            
        )
        read_only_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
    

        password = validated_data.pop('password', "")
        user = CustomUser.objects.create_user(**validated_data, password=password)
        print(password) 
        if not password:
            raise serializers.ValidationError({"error": "Password is required."})
        else:
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