from rest_framework import serializers
from rest_framework_simplejwt.serializers import PasswordField


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        error_messages={
            'required': 'Username is required'
        }
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'the password is required'
        }
    )