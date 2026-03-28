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
from .comments_serializers import (
    CommentsSerializer,
    CommentsCreateUpdateSerializer,
    CommentsDetailSerializer,
    CommentsListSerializer,
    CommentsDeletedListSerializer
)

from .surveys_serializers import (
    SurveysSerializer,
    SurveysCreateUpdateSerializer,
    SurveysDetailSerializer,
    SurveysListSerializer,
    SurveysDeletedListSerializer
)

from .survey_options_serializers import (
    SurveyOptionsSerializer,
    SurveyOptionsCreateUpdateSerializer,
    SurveyOptionsDetailSerializer,
    SurveyOptionsListSerializer,
    SurveyOptionsDeletedListSerializer
)

from .events_serializers import (
    EventsSerializer,
    EventsCreateUpdateSerializer,
    EventsDetailSerializer,
    EventsListSerializer,
    EventsDeletedListSerializer
)