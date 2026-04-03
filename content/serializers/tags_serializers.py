from rest_framework import serializers
from content.models import Tags

class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = [
            'id', 
            'name_ar', 
            'name_ku', 
            'name_en', 
            'slug', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TagsCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ['name_ar', 'name_ku', 'name_en', 'slug']
        extra_kwargs = {
            'name_ar': {'required': True, 'error_messages': {'required': 'Arabic name is required'}},
            'name_ku': {'required': True, 'error_messages': {'required': 'Kurdish name is required'}},
            'name_en': {'required': True, 'error_messages': {'required': 'English name is required'}},
        }
    
    def validate_name_ar(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Arabic name is required")
        
        if self.instance and self.instance.name_ar == value:
            return value
        
        if Tags.objects.filter(name_ar=value).exists():
            raise serializers.ValidationError("Arabic name already exists")
        
        return value
    
    def validate_name_ku(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Kurdish name is required")
        
        if self.instance and self.instance.name_ku == value:
            return value
        
        if Tags.objects.filter(name_ku=value).exists():
            raise serializers.ValidationError("Kurdish name already exists")
        
        return value
    
    def validate_name_en(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("English name is required")
        
        if self.instance and self.instance.name_en == value:
            return value
        
        if Tags.objects.filter(name_en=value).exists():
            raise serializers.ValidationError("English name already exists")
        
        return value
    
   
    
    def validate(self, data):
        if self.instance is None:
            required_fields = ['name_ar', 'name_ku', 'name_en']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"This field is required"})
        
        return data
    
    def create(self, validated_data):
        tag = Tags.objects.create(
            name_ar=validated_data['name_ar'],
            name_ku=validated_data['name_ku'],
            name_en=validated_data['name_en'],
        )
        return tag
    
    def update(self, instance, validated_data):
        instance.name_ar = validated_data.get('name_ar', instance.name_ar)
        instance.name_ku = validated_data.get('name_ku', instance.name_ku)
        instance.name_en = validated_data.get('name_en', instance.name_en)
        
        instance.save()
        return instance


class TagsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


class TagsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ['id', 'name_ar', 'name_ku', 'name_en', 'slug', 'created_at']