# content/serializers/posts_serializers.py
from rest_framework import serializers
from content.models import Posts, ContentType, Language, Tags
import re
import json

class PostsSerializer(serializers.ModelSerializer):
    featured_image = serializers.SerializerMethodField()
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    category_name = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = Posts
        fields = [
            'id',
            'original_post',
            'author',
            'author_name',
            'category',
            'category_name',
            'content_type',
            'content_type_display',
            'language',
            'language_display',
            'title',
            'excerpt',
            'content',
            'meta_title',
            'meta_description',
            'featured_image',
            'tags',
            'view_count',
            'published_at',
            'is_published',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'view_count', 'created_at', 'updated_at']
        extra_kwargs = {
            'title': {'required': True, 'error_messages': {'required': 'Title is required'}},
            'content': {'required': True, 'error_messages': {'required': 'Content is required'}},
            'content_type': {'required': True, 'error_messages': {'required': 'Content type is required'}},
            'language': {'required': True, 'error_messages': {'required': 'Language is required'}},
            'category': {'required': True, 'error_messages': {'required': 'Category is required'}},
            'author': {'required': True, 'error_messages': {'required': 'Author is required'}},
            'excerpt': {'required': False, 'allow_null': True, 'allow_blank': True},
            'meta_title': {'required': False, 'allow_null': True, 'allow_blank': True},
            'meta_description': {'required': False, 'allow_null': True, 'allow_blank': True},
            'is_published': {'required': False, 'default': False},
            'published_at': {'required': False, 'allow_null': True},
            'original_post': {'required': False, 'allow_null': True},
        }
    
    def get_featured_image(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None
    
    def get_category_name(self, obj):
        if obj.category:
            request = self.context.get('request')
            if request:
                language = request.query_params.get('lang', 'ar')
                names = {
                    'ar': obj.category.name_ar,
                    'ku': obj.category.name_ku,
                    'en': obj.category.name_en
                }
                return names.get(language, obj.category.name_ar)
            return obj.category.name_ar
        return None
    
    def get_tags(self, obj):
        tags = obj.tags.filter(deleted_at__isnull=True)
        request = self.context.get('request')
        language = request.query_params.get('lang', 'ar') if request else 'ar'
        
        return [
            {
                'id': tag.id,
                'name': self._get_tag_name(tag, language),  
                'name_ar': tag.name_ar,
                'name_ku': tag.name_ku,
                'name_en': tag.name_en,
                'slug': tag.slug
            }
            for tag in tags
        ]
    
    def _get_tag_name(self, tag, language):
        names = {
            'ar': tag.name_ar,
            'ku': tag.name_ku,
            'en': tag.name_en
        }
        return names.get(language, tag.name_ar)


class PostsCreateUpdateSerializer(serializers.ModelSerializer):
    featured_image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Upload featured image"
    )
    
    tags = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Tag IDs separated by commas (e.g., 1,2,3) or JSON array [1,2,3]"
    )
    
    class Meta:
        model = Posts
        fields = [
            'original_post',
            'author',
            'category',
            'tags',
            'content_type',
            'language',
            'title',
            'excerpt',
            'content',
            'meta_title',
            'meta_description',
            'featured_image',
            'is_published',
            'published_at'
        ]
        extra_kwargs = {
            'title': {'required': True, 'error_messages': {'required': 'Title is required'}},
            'content': {'required': True, 'error_messages': {'required': 'Content is required'}},
            'content_type': {'required': True, 'error_messages': {'required': 'Content type is required'}},
            'language': {'required': True, 'error_messages': {'required': 'Language is required'}},
            'category': {'required': True, 'error_messages': {'required': 'Category is required'}},
            'author': {'required': True, 'error_messages': {'required': 'Author is required'}},
            'tags': {'required': False},
            'featured_image': {'required': False, 'allow_null': True},
            'excerpt': {'required': False, 'allow_null': True, 'allow_blank': True},
            'meta_title': {'required': False, 'allow_null': True, 'allow_blank': True},
            'meta_description': {'required': False, 'allow_null': True, 'allow_blank': True},
            'is_published': {'required': False, 'default': False},
            'published_at': {'required': False, 'allow_null': True},
            'original_post': {'required': False, 'allow_null': True},
        }
    
    def _parse_tags(self, value):
        if not value or value.strip() == '':
            return []
        
        if isinstance(value, list):
            return value
        
        if isinstance(value, str):
            value = value.strip()
            
            if value.startswith('[') and value.endswith(']'):
                try:
                    tag_list = json.loads(value)
                    if isinstance(tag_list, list):
                        return [int(tag) for tag in tag_list if tag]
                except (json.JSONDecodeError, ValueError):
                    pass
            
            try:
                return [int(id_str.strip()) for id_str in value.split(',') if id_str.strip()]
            except ValueError:
                raise serializers.ValidationError("Tags must be comma-separated numbers (e.g., 1,2,3)")
        
        raise serializers.ValidationError("Invalid tags format")
    
    def validate_category(self, value):
        if not value:
            raise serializers.ValidationError("Category is required")
        return value
    
    def validate_author(self, value):
        if not value:
            raise serializers.ValidationError("Author is required")
        return value
    
    def validate_content_type(self, value):
        if not value:
            raise serializers.ValidationError("Content type is required")
        
        if value not in dict(ContentType.choices).keys():
            raise serializers.ValidationError(f"Invalid content type. Choices: {', '.join(dict(ContentType.choices).keys())}")
        
        return value
    
    def validate_language(self, value):
        if not value:
            raise serializers.ValidationError("Language is required")
        
        if value not in dict(Language.choices).keys():
            raise serializers.ValidationError(f"Invalid language. Choices: {', '.join(dict(Language.choices).keys())}")
        
        return value
    
    def validate_title(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Title is required")
        
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        
        if len(value) > 500:
            raise serializers.ValidationError("Title cannot exceed 500 characters")
        
        return value
    
    def validate_content(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Content is required")
        
        return value
    
    def validate(self, data):
        if self.instance is None:
            required_fields = ['title', 'content', 'author', 'category', 'content_type', 'language']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})
        
        tags_value = data.get('tags')
        if tags_value:
            try:
                tags_list = self._parse_tags(tags_value)
                
                if tags_list:
                    existing_tags = Tags.objects.filter(id__in=tags_list, deleted_at__isnull=True)
                    if len(existing_tags) != len(tags_list):
                        valid_ids = list(Tags.objects.filter(deleted_at__isnull=True).values_list('id', flat=True))
                        raise serializers.ValidationError({
                            'tags': f"One or more tags do not exist. Valid tag IDs: {valid_ids}"
                        })
                
                data['tags'] = tags_list
            except serializers.ValidationError as e:
                raise e
            except Exception as e:
                raise serializers.ValidationError({'tags': str(e)})
        else:
            data['tags'] = []
        
        return data
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        
        if validated_data.get('is_published') and not validated_data.get('published_at'):
            from django.utils import timezone
            validated_data['published_at'] = timezone.now()
        
        post = Posts.objects.create(**validated_data)
        
        if tags:
            post.tags.set(tags)
        
        return post
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        
        if validated_data.get('is_published') and not instance.published_at:
            from django.utils import timezone
            validated_data['published_at'] = timezone.now()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        
        return instance


class PostsDetailSerializer(serializers.ModelSerializer):
    featured_image = serializers.SerializerMethodField()
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    author_slug = serializers.CharField(source='author.slug', read_only=True)
    category_name = serializers.SerializerMethodField()
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    original_post_title = serializers.CharField(source='original_post.title', read_only=True)
    translations = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = Posts
        fields = '__all__'
        read_only_fields = ['id', 'view_count', 'created_at', 'updated_at', 'deleted_at']
    
    def get_featured_image(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None
    
    def get_category_name(self, obj):
        if obj.category:
            request = self.context.get('request')
            if request:
                language = request.query_params.get('lang', 'ar')
                names = {
                    'ar': obj.category.name_ar,
                    'ku': obj.category.name_ku,
                    'en': obj.category.name_en
                }
                return names.get(language, obj.category.name_ar)
            return obj.category.name_ar
        return None
    
    def get_tags(self, obj):
        tags = obj.tags.filter(deleted_at__isnull=True)
        request = self.context.get('request')
        language = request.query_params.get('lang', 'ar') if request else 'ar'
        
        return [
            {
                'id': tag.id,
                'name': self._get_tag_name(tag, language), 
                'name_ar': tag.name_ar,
                'name_ku': tag.name_ku,
                'name_en': tag.name_en,
                'slug': tag.slug
            }
            for tag in tags
        ]
    
    def _get_tag_name(self, tag, language):
        names = {
            'ar': tag.name_ar,
            'ku': tag.name_ku,
            'en': tag.name_en
        }
        return names.get(language, tag.name_ar)

    
    def get_translations(self, obj):
        if obj.original_post:
            translations = Posts.objects.filter(original_post=obj.original_post)
        else:
            translations = Posts.objects.filter(original_post=obj)
        
        return PostsListSerializer(translations, many=True, context=self.context).data


class PostsListSerializer(serializers.ModelSerializer):
    featured_image = serializers.SerializerMethodField()
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    category_name = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = Posts
        fields = [
            'id',
            'title',
            'excerpt',
            'featured_image',
            'author_name',
            'category_name',
            'tags',
            'content_type',
            'content_type_display',
            'language',
            'language_display',
            'view_count',
            'published_at',
            'is_published',
            'created_at'
        ]
    
    def get_featured_image(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None
    
    def get_category_name(self, obj):
        if obj.category:
            request = self.context.get('request')
            if request:
                language = request.query_params.get('lang', 'ar')
                names = {
                    'ar': obj.category.name_ar,
                    'ku': obj.category.name_ku,
                    'en': obj.category.name_en
                }
                return names.get(language, obj.category.name_ar)
            return obj.category.name_ar
        return None
    
    def get_tags(self, obj):
        tags = obj.tags.filter(deleted_at__isnull=True)
        request = self.context.get('request')
        language = request.query_params.get('lang', 'ar') if request else 'ar'
        
        return [
            {
                'id': tag.id,
                'name': self._get_tag_name(tag, language), 
                'slug': tag.slug
            }
            for tag in tags
        ]
    
    def _get_tag_name(self, tag, language):
        names = {
            'ar': tag.name_ar,
            'ku': tag.name_ku,
            'en': tag.name_en
        }
        return names.get(language, tag.name_ar)


class PostsDeletedListSerializer(serializers.ModelSerializer):
    featured_image = serializers.SerializerMethodField()
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    category_name = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = Posts
        fields = [
            'id',
            'title',
            'excerpt',
            'featured_image',
            'author_name',
            'category_name',
            'tags',
            'content_type',
            'content_type_display',
            'language',
            'language_display',
            'view_count',
            'published_at',
            'is_published',
            'created_at',
            'deleted_at'
        ]
    
    def get_featured_image(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None
    
    def get_category_name(self, obj):
        if obj.category:
            return obj.category.name_ar
        return None
    
    def get_tags(self, obj):
        tags = obj.tags.filter(deleted_at__isnull=True)
        return [
            {
                'id': tag.id,
                'name_ar': tag.name_ar,
                'name_ku': tag.name_ku,
                'name_en': tag.name_en,
                'slug': tag.slug
            }
            for tag in tags
        ]