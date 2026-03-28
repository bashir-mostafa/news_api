# content/serializers/comments_serializers.py
from rest_framework import serializers
from content.models import Comments
import re

class CommentsSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    
    class Meta:
        model = Comments
        fields = [
            'id',
            'post',
            'post_title',
            'name',
            'email',
            'comment',
            'is_approved',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommentsCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ['post', 'name', 'email', 'comment', 'is_approved']
        extra_kwargs = {
            'post': {'required': True, 'error_messages': {'required': 'Post is required'}},
            'name': {'required': True, 'error_messages': {'required': 'Name is required'}},
            'email': {'required': True, 'error_messages': {'required': 'Email is required'}},
            'comment': {'required': True, 'error_messages': {'required': 'Comment is required'}},
            'is_approved': {'required': False, 'default': False},
        }
    
    def validate_name(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Name is required")
        
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long")
        
        if len(value) > 255:
            raise serializers.ValidationError("Name cannot exceed 255 characters")
        
        return value
    
    def validate_email(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Email is required")
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError("Enter a valid email address")
        
        return value
    
    def validate_comment(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Comment is required")
        
        if len(value) < 3:
            raise serializers.ValidationError("Comment must be at least 3 characters long")
        
        return value
    
    def validate_post(self, value):
        if not value:
            raise serializers.ValidationError("Post is required")
        
        # التحقق من وجود المقال وعدم حذفه
        from content.models import Posts
        if not Posts.objects.filter(id=value.id, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Post does not exist or has been deleted")
        
        return value
    
    def validate(self, data):
        if self.instance is None:
            required_fields = ['post', 'name', 'email', 'comment']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})
        
        return data
    
    def create(self, validated_data):
        comment = Comments.objects.create(**validated_data)
        return comment
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CommentsDetailSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_slug = serializers.CharField(source='post.slug', read_only=True)
    
    class Meta:
        model = Comments
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


class CommentsListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    
    class Meta:
        model = Comments
        fields = ['id', 'post', 'post_title', 'name', 'email', 'comment', 'is_approved', 'created_at']


class CommentsDeletedListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    
    class Meta:
        model = Comments
        fields = ['id', 'post', 'post_title', 'name', 'email', 'comment', 'is_approved', 'created_at', 'deleted_at']