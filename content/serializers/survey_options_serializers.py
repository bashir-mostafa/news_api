# content/serializers/survey_options_serializers.py
from rest_framework import serializers
from content.models import SurveyOptions, Surveys

class SurveyOptionsSerializer(serializers.ModelSerializer):
    survey_question = serializers.CharField(source='survey.question', read_only=True)
    post_title = serializers.CharField(source='survey.post.title', read_only=True)
    
    class Meta:
        model = SurveyOptions
        fields = [
            'id',
            'survey',
            'survey_question',
            'post_title',
            'option_text',
            'vote_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'vote_count', 'created_at', 'updated_at']


class SurveyOptionsCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyOptions
        fields = ['survey', 'option_text', 'vote_count']
        extra_kwargs = {
            'survey': {'required': True, 'error_messages': {'required': 'Survey is required'}},
            'option_text': {'required': True, 'error_messages': {'required': 'Option text is required'}},
            'vote_count': {'required': False, 'default': 0},
        }
    
    def validate_option_text(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Option text is required")
        
        if len(value) < 2:
            raise serializers.ValidationError("Option text must be at least 2 characters long")
        
        if len(value) > 255:
            raise serializers.ValidationError("Option text cannot exceed 255 characters")
        
        return value
    
    def validate_survey(self, value):
        if not value:
            raise serializers.ValidationError("Survey is required")
        
        # التحقق من وجود الاستبيان وعدم حذفه
        if not Surveys.objects.filter(id=value.id, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Survey does not exist or has been deleted")
        
        # التحقق من أن الاستبيان نشط
        if not value.is_active:
            raise serializers.ValidationError("Cannot add options to an inactive survey")
        
        return value
    
    def validate_vote_count(self, value):
        if value < 0:
            raise serializers.ValidationError("Vote count cannot be negative")
        return value
    
    def validate(self, data):
        if self.instance is None:
            required_fields = ['survey', 'option_text']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})
        
        return data
    
    def create(self, validated_data):
        option = SurveyOptions.objects.create(**validated_data)
        return option
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SurveyOptionsDetailSerializer(serializers.ModelSerializer):
    survey_question = serializers.CharField(source='survey.question', read_only=True)
    post_title = serializers.CharField(source='survey.post.title', read_only=True)
    post_id = serializers.IntegerField(source='survey.post.id', read_only=True)
    
    class Meta:
        model = SurveyOptions
        fields = '__all__'
        read_only_fields = ['id', 'vote_count', 'created_at', 'updated_at', 'deleted_at']


class SurveyOptionsListSerializer(serializers.ModelSerializer):
    survey_question = serializers.CharField(source='survey.question', read_only=True)
    
    class Meta:
        model = SurveyOptions
        fields = [
            'id',
            'survey',
            'survey_question',
            'option_text',
            'vote_count',
            'created_at'
        ]


class SurveyOptionsDeletedListSerializer(serializers.ModelSerializer):
    survey_question = serializers.CharField(source='survey.question', read_only=True)
    post_title = serializers.CharField(source='survey.post.title', read_only=True)
    
    class Meta:
        model = SurveyOptions
        fields = [
            'id',
            'survey',
            'survey_question',
            'post_title',
            'option_text',
            'vote_count',
            'created_at',
            'deleted_at'
        ]