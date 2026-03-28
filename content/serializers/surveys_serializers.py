# content/serializers/surveys_serializers.py
from rest_framework import serializers
from content.models import Surveys, Posts
from django.utils import timezone

class SurveysSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    is_closed = serializers.SerializerMethodField()
    
    class Meta:
        model = Surveys
        fields = [
            'id',
            'post',
            'post_title',
            'question',
            'is_active',
            'is_closed',
            'closes_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_closed(self, obj):
        """التحقق مما إذا كان الاستبيان مغلقاً"""
        if obj.closes_at and obj.closes_at <= timezone.now():
            return True
        return False


class SurveysCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Surveys
        fields = ['post', 'question', 'is_active', 'closes_at']
        extra_kwargs = {
            'post': {'required': True, 'error_messages': {'required': 'Post is required'}},
            'question': {'required': True, 'error_messages': {'required': 'Question is required'}},
            'is_active': {'required': False, 'default': True},
            'closes_at': {'required': False, 'allow_null': True},
        }
    
    def validate_question(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Question is required")
        
        if len(value) < 3:
            raise serializers.ValidationError("Question must be at least 3 characters long")
        
        if len(value) > 255:
            raise serializers.ValidationError("Question cannot exceed 255 characters")
        
        return value
    
    def validate_post(self, value):
        if not value:
            raise serializers.ValidationError("Post is required")
        
        # التحقق من وجود المقال وعدم حذفه
        if not Posts.objects.filter(id=value.id, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Post does not exist or has been deleted")
        
        return value
    
    def validate_closes_at(self, value):
        """التحقق من أن تاريخ الإغلاق في المستقبل"""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Closing date must be in the future")
        return value
    
    def validate(self, data):
        if self.instance is None:
            required_fields = ['post', 'question']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})
        
        return data
    
    def create(self, validated_data):
        survey = Surveys.objects.create(**validated_data)
        return survey
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SurveysDetailSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_slug = serializers.CharField(source='post.slug', read_only=True)
    is_closed = serializers.SerializerMethodField()
    
    class Meta:
        model = Surveys
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    
    def get_is_closed(self, obj):
        """التحقق مما إذا كان الاستبيان مغلقاً"""
        if obj.closes_at and obj.closes_at <= timezone.now():
            return True
        return False


class SurveysListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    is_closed = serializers.SerializerMethodField()
    
    class Meta:
        model = Surveys
        fields = [
            'id', 
            'post', 
            'post_title', 
            'question', 
            'is_active', 
            'is_closed',
            'closes_at', 
            'created_at'
        ]
    
    def get_is_closed(self, obj):
        """التحقق مما إذا كان الاستبيان مغلقاً"""
        if obj.closes_at and obj.closes_at <= timezone.now():
            return True
        return False


class SurveysDeletedListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    is_closed = serializers.SerializerMethodField()
    
    class Meta:
        model = Surveys
        fields = [
            'id', 
            'post', 
            'post_title', 
            'question', 
            'is_active', 
            'is_closed',
            'closes_at', 
            'created_at', 
            'deleted_at'
        ]
    
    def get_is_closed(self, obj):
        """التحقق مما إذا كان الاستبيان مغلقاً"""
        if obj.closes_at and obj.closes_at <= timezone.now():
            return True
        return False