# content/serializers/events_serializers.py
from rest_framework import serializers
from content.models import Events, Posts
from django.utils import timezone

class EventsSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    is_past = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    
    class Meta:
        model = Events
        fields = [
            'id',
            'post',
            'post_title',
            'event_type',
            'event_date',
            'location',
            'attendees_count',
            'is_past',
            'is_upcoming',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'attendees_count', 'created_at', 'updated_at']
    
    def get_is_past(self, obj):
        """التحقق مما إذا كان الحدث قد مضى"""
        return obj.event_date < timezone.now()
    
    def get_is_upcoming(self, obj):
        """التحقق مما إذا كان الحدث قادم"""
        return obj.event_date > timezone.now()


class EventsCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ['post', 'event_type', 'event_date', 'location', 'attendees_count']
        extra_kwargs = {
            'post': {'required': True, 'error_messages': {'required': 'Post is required'}},
            'event_type': {'required': True, 'error_messages': {'required': 'Event type is required'}},
            'event_date': {'required': True, 'error_messages': {'required': 'Event date is required'}},
            'location': {'required': True, 'error_messages': {'required': 'Location is required'}},
            'attendees_count': {'required': False, 'default': 0},
        }
    
    def validate_event_type(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Event type is required")
        
        if len(value) < 3:
            raise serializers.ValidationError("Event type must be at least 3 characters long")
        
        if len(value) > 50:
            raise serializers.ValidationError("Event type cannot exceed 50 characters")
        
        return value
    
    def validate_event_date(self, value):
        if not value:
            raise serializers.ValidationError("Event date is required")
        
        # التحقق من أن تاريخ الحدث في المستقبل (اختياري)
        if value < timezone.now():
            raise serializers.ValidationError("Event date cannot be in the past")
        
        return value
    
    def validate_location(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Location is required")
        
        if len(value) < 3:
            raise serializers.ValidationError("Location must be at least 3 characters long")
        
        if len(value) > 255:
            raise serializers.ValidationError("Location cannot exceed 255 characters")
        
        return value
    
    def validate_attendees_count(self, value):
        if value < 0:
            raise serializers.ValidationError("Attendees count cannot be negative")
        return value
    
    def validate_post(self, value):
        if not value:
            raise serializers.ValidationError("Post is required")
        
        # التحقق من وجود المقال وعدم حذفه
        if not Posts.objects.filter(id=value.id, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Post does not exist or has been deleted")
        
        return value
    
    def validate(self, data):
        if self.instance is None:
            required_fields = ['post', 'event_type', 'event_date', 'location']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})
        
        return data
    
    def create(self, validated_data):
        event = Events.objects.create(**validated_data)
        return event
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EventsDetailSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_slug = serializers.CharField(source='post.slug', read_only=True)
    is_past = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    
    class Meta:
        model = Events
        fields = '__all__'
        read_only_fields = ['id', 'attendees_count', 'created_at', 'updated_at', 'deleted_at']
    
    def get_is_past(self, obj):
        """التحقق مما إذا كان الحدث قد مضى"""
        return obj.event_date < timezone.now()
    
    def get_is_upcoming(self, obj):
        """التحقق مما إذا كان الحدث قادم"""
        return obj.event_date > timezone.now()


class EventsListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    is_past = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    
    class Meta:
        model = Events
        fields = [
            'id',
            'post',
            'post_title',
            'event_type',
            'event_date',
            'location',
            'attendees_count',
            'is_past',
            'is_upcoming',
            'created_at'
        ]
    
    def get_is_past(self, obj):
        """التحقق مما إذا كان الحدث قد مضى"""
        return obj.event_date < timezone.now()
    
    def get_is_upcoming(self, obj):
        """التحقق مما إذا كان الحدث قادم"""
        return obj.event_date > timezone.now()


class EventsDeletedListSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    is_past = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    
    class Meta:
        model = Events
        fields = [
            'id',
            'post',
            'post_title',
            'event_type',
            'event_date',
            'location',
            'attendees_count',
            'is_past',
            'is_upcoming',
            'created_at',
            'deleted_at'
        ]
    
    def get_is_past(self, obj):
        """التحقق مما إذا كان الحدث قد مضى"""
        return obj.event_date < timezone.now()
    
    def get_is_upcoming(self, obj):
        """التحقق مما إذا كان الحدث قادم"""
        return obj.event_date > timezone.now()