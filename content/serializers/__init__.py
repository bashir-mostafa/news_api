# content/serializers/__init__.py
from .tags_serializers import (
    TagsSerializer,
    TagsCreateUpdateSerializer,
    TagsDetailSerializer,
    TagsListSerializer
)

from .authors_serializers import (
    AuthorsSerializer,
    AuthorsCreateUpdateSerializer,
    AuthorsDetailSerializer,
    AuthorsListSerializer
)

from .categories_serializers import (
    CategoriesSerializer,
    CategoriesCreateUpdateSerializer,
    CategoriesDetailSerializer,
    CategoriesListSerializer
)

from .posts_serializers import (
    PostsSerializer,
    PostsCreateUpdateSerializer,
    PostsDetailSerializer,
    PostsListSerializer,
    PostsDeletedListSerializer
)