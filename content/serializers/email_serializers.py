# serializers.py
from rest_framework import serializers
from rest_framework.views import APIView
class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()    # ← يتحقق إنه إيميل صحيح
    message = serializers.CharField()  # ← يتحقق إنه نص موجود