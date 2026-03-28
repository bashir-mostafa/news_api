from django.urls import path
from content.views import (
    events_views,
    posts_views,
    comments_views, 
    categories_views,
    authors_views, 
    tags_views,
    surveys_views,
    survey_options_views,
    publications_views
    )

app_name = 'tags'

urlpatterns = [
     # ============ POSTS URLs ============
    # List and Create
    path('posts/', posts_views.PostListCreateView.as_view(), name='post-list-create'),
    
    # Retrieve, Update, Delete by ID
    path('posts/<int:id>/', posts_views.PostRetrieveUpdateDeleteView.as_view(), name='post-detail'),
    
    # Get by ID (بدلاً من Slug)
    path('posts/id/<int:id>/', posts_views.PostByIdView.as_view(), name='post-by-id'),
    
    # Deleted Posts
    path('posts/deleted/', posts_views.PostDeletedListView.as_view(), name='post-deleted-list'),
    
    # Statistics
    path('posts/statistics/', posts_views.PostStatisticsView.as_view(), name='post-statistics'),
    
    # Publish / Unpublish
    path('posts/publish/<int:id>/', posts_views.PostPublishView.as_view(), name='post-publish'),
    path('posts/unpublish/<int:id>/', posts_views.PostUnpublishView.as_view(), name='post-unpublish'),
    
    # Increment View Count
    path('posts/increment-view/<int:id>/', posts_views.PostIncrementViewView.as_view(), name='post-increment-view'),
    
    # Restore
    path('posts/<int:id>/restore/', posts_views.PostRestoreView.as_view(), name='post-restore'),
    
    # Bulk Operations
    path('posts/bulk-delete/', posts_views.PostBulkDeleteView.as_view(), name='post-bulk-delete'),
    path('posts/bulk-restore/', posts_views.PostBulkRestoreView.as_view(), name='post-bulk-restore'),
    path('posts/bulk-hard-delete/', posts_views.PostBulkHardDeleteView.as_view(), name='post-bulk-hard-delete'),
    
    # Hard Delete
    path('posts/<int:id>/hard-delete/', posts_views.PostHardDeleteView.as_view(), name='post-hard-delete'),
    # ============ BASIC CRUD ============
    # GET (list all tags), POST (create new tag)
    path('tags/', tags_views.TagListCreateView.as_view(), name='tag-list-create'),
    
    # GET (detail), PUT (update), PATCH (partial update), DELETE (soft delete)
    path('tags/<int:id>/', tags_views.TagRetrieveUpdateDeleteView.as_view(), name='tag-detail'),
    
    # ============ HARD DELETE ============
    # DELETE (permanent delete - admin only)
    path('tags/<int:id>/hard-delete/', tags_views.TagHardDeleteView.as_view(), name='tag-hard-delete'),
     # DELETE (permanent delete multiple tags - admin only)
    path('tags/bulk-hard-delete/', tags_views.TagBulkHardDeleteView.as_view(), name='tag-bulk-hard-delete'),
    # ============ RESTORE SOFT DELETED ============
    # POST (restore soft deleted tag)
    path('tags/<int:id>/restore/', tags_views.TagRestoreView.as_view(), name='tag-restore'),
    
    # ============ BULK OPERATIONS ============
    # DELETE (bulk soft delete)
    path('tags/bulk-delete/', tags_views.TagBulkDeleteView.as_view(), name='tag-bulk-delete'),
    path('tags/bulk-restore/', tags_views.TagBulkRestoreView.as_view(), name='tag-bulk-restore'),
    # ========================================================================================================

    # ========================================================================================================
    # Authors URLs
    # ========================================================================================================
    # ============ BASIC CRUD ============
    # GET (list all tags), POST (create new tag)
    path('authors/', authors_views.AuthorListCreateView.as_view(), name='author-list-create'),
    # GET (detail), PUT (update), PATCH (partial update), DELETE (soft delete)
    path('authors/<int:id>/', authors_views.AuthorRetrieveUpdateDeleteView.as_view(), name='author-detail'),
    
    # ============ HARD DELETE ============
    # DELETE (bulk soft delete)
    path('authors/<int:id>/hard-delete/', authors_views.AuthorHardDeleteView.as_view(), name='author-hard-delete'),
    # DELETE (permanent delete multiple authors - admin only)
    path('authors/bulk-hard-delete/', authors_views.AuthorBulkHardDeleteView.as_view(), name='author-bulk-hard-delete'),
    # ============ RESTORE SOFT DELETED ============
    # POST (restore soft deleted authors)
    path('authors/<int:id>/restore/', authors_views.AuthorRestoreView.as_view(), name='author-restore'),
    
    # ============ BULK OPERATIONS ============
    path('authors/bulk-delete/', authors_views.AuthorBulkDeleteView.as_view(), name='author-bulk-delete'),
    path('authors/bulk-restore/', authors_views.AuthorBulkRestoreView.as_view(), name='author-bulk-restore'),
   # ============ BASIC CRUD ============
    # GET (list all categories), POST (create new category)
    path('categories/', categories_views.CategoryListCreateView.as_view(), name='category-list-create'),
    # GET (detail), PUT (update), PATCH (partial update), DELETE (soft delete)
    path('categories/<int:id>/', categories_views.CategoryRetrieveUpdateDeleteView.as_view(), name='category-detail'),
    
    # ============ HARD DELETE ============
    # DELETE (permanent delete - admin only)
    path('categories/<int:id>/hard-delete/', categories_views.CategoryHardDeleteView.as_view(), name='category-hard-delete'),
    path('categories/bulk-hard-delete/', categories_views.CategoryBulkHardDeleteView.as_view(), name='category-bulk-hard-delete'),

    # ============ RESTORE SOFT DELETED ============
    # POST (restore soft deleted category)
    path('categories/<int:id>/restore/', categories_views.CategoryRestoreView.as_view(), name='category-restore'),
    
    # ============ BULK OPERATIONS ============
    # DELETE (bulk soft delete)
    path('categories/bulk-delete/', categories_views.CategoryBulkDeleteView.as_view(), name='category-bulk-delete'),
    # POST (bulk restore)
    path('categories/bulk-restore/', categories_views.CategoryBulkRestoreView.as_view(), name='category-bulk-restore'),

    # ============ COMMENTS URLs ============
    # Basic CRUD
    path('comments/', comments_views.CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:id>/', comments_views.CommentRetrieveUpdateDeleteView.as_view(), name='comment-detail'),
    
    # Deleted Comments
    path('comments/deleted/', comments_views.CommentDeletedListView.as_view(), name='comment-deleted-list'),
    
    # Approve / Unapprove
    path('comments/approve/<int:id>/', comments_views.CommentApproveView.as_view(), name='comment-approve'),
    path('comments/unapprove/<int:id>/', comments_views.CommentUnapproveView.as_view(), name='comment-unapprove'),
    
    # Get Comments by Post
    path('comments/by-post/<int:post_id>/', comments_views.CommentsByPostView.as_view(), name='comments-by-post'),
    
    # Restore
    path('comments/<int:id>/restore/', comments_views.CommentRestoreView.as_view(), name='comment-restore'),
    
    # Bulk Operations
    path('comments/bulk-delete/', comments_views.CommentBulkDeleteView.as_view(), name='comment-bulk-delete'),
    path('comments/bulk-restore/', comments_views.CommentBulkRestoreView.as_view(), name='comment-bulk-restore'),
    path('comments/bulk-hard-delete/', comments_views.CommentBulkHardDeleteView.as_view(), name='comment-bulk-hard-delete'),
    
    # Hard Delete
    path('comments/<int:id>/hard-delete/', comments_views.CommentHardDeleteView.as_view(), name='comment-hard-delete'),

        # ============ SURVEYS URLs ============
    # Basic CRUD
    path('surveys/', surveys_views.SurveyListCreateView.as_view(), name='survey-list-create'),
    path('surveys/<int:id>/', surveys_views.SurveyRetrieveUpdateDeleteView.as_view(), name='survey-detail'),
    
    # Deleted Surveys
    path('surveys/deleted/', surveys_views.SurveyDeletedListView.as_view(), name='survey-deleted-list'),
    
    # Activate / Deactivate
    path('surveys/activate/<int:id>/', surveys_views.SurveyActivateView.as_view(), name='survey-activate'),
    path('surveys/deactivate/<int:id>/', surveys_views.SurveyDeactivateView.as_view(), name='survey-deactivate'),
    
    # Get Surveys by Post
    path('surveys/by-post/<int:post_id>/', surveys_views.SurveysByPostView.as_view(), name='surveys-by-post'),
    
    # Restore
    path('surveys/<int:id>/restore/', surveys_views.SurveyRestoreView.as_view(), name='survey-restore'),
    
    # Bulk Operations
    path('surveys/bulk-delete/', surveys_views.SurveyBulkDeleteView.as_view(), name='survey-bulk-delete'),
    path('surveys/bulk-restore/', surveys_views.SurveyBulkRestoreView.as_view(), name='survey-bulk-restore'),
    path('surveys/bulk-hard-delete/', surveys_views.SurveyBulkHardDeleteView.as_view(), name='survey-bulk-hard-delete'),
    
    # Hard Delete
    path('surveys/<int:id>/hard-delete/', surveys_views.SurveyHardDeleteView.as_view(), name='survey-hard-delete'),

    # ============ SURVEY OPTIONS URLs ============
    # Basic CRUD
    path('survey-options/', survey_options_views.SurveyOptionListCreateView.as_view(), name='survey-option-list-create'),
    path('survey-options/<int:id>/', survey_options_views.SurveyOptionRetrieveUpdateDeleteView.as_view(), name='survey-option-detail'),
    
    # Deleted Survey Options
    path('survey-options/deleted/', survey_options_views.SurveyOptionDeletedListView.as_view(), name='survey-option-deleted-list'),
    
    # Vote
    path('survey-options/vote/<int:id>/', survey_options_views.SurveyOptionVoteView.as_view(), name='survey-option-vote'),
    
    # Get Options by Survey
    path('survey-options/by-survey/<int:survey_id>/', survey_options_views.SurveyOptionsBySurveyView.as_view(), name='survey-options-by-survey'),
    
    # Restore
    path('survey-options/<int:id>/restore/', survey_options_views.SurveyOptionRestoreView.as_view(), name='survey-option-restore'),
    
    # Bulk Operations
    path('survey-options/bulk-delete/', survey_options_views.SurveyOptionBulkDeleteView.as_view(), name='survey-option-bulk-delete'),
    path('survey-options/bulk-restore/', survey_options_views.SurveyOptionBulkRestoreView.as_view(), name='survey-option-bulk-restore'),
    path('survey-options/bulk-hard-delete/', survey_options_views.SurveyOptionBulkHardDeleteView.as_view(), name='survey-option-bulk-hard-delete'),
    
    # Hard Delete
    path('survey-options/<int:id>/hard-delete/', survey_options_views.SurveyOptionHardDeleteView.as_view(), name='survey-option-hard-delete'),


 # ============ EVENTS URLs ============
    # Basic CRUD
    path('events/', events_views.EventListCreateView.as_view(), name='event-list-create'),
    path('events/<int:id>/', events_views.EventRetrieveUpdateDeleteView.as_view(), name='event-detail'),
    
    # Deleted Events
    path('events/deleted/', events_views.EventDeletedListView.as_view(), name='event-deleted-list'),
    
    # Attendees Management
    path('events/increment-attendees/<int:id>/', events_views.EventIncrementAttendeesView.as_view(), name='event-increment-attendees'),
    path('events/decrement-attendees/<int:id>/', events_views.EventDecrementAttendeesView.as_view(), name='event-decrement-attendees'),
    
    # Get Events by Post
    path('events/by-post/<int:post_id>/', events_views.EventsByPostView.as_view(), name='events-by-post'),
    
    # Restore
    path('events/<int:id>/restore/', events_views.EventRestoreView.as_view(), name='event-restore'),
    
    # Bulk Operations
    path('events/bulk-delete/', events_views.EventBulkDeleteView.as_view(), name='event-bulk-delete'),
    path('events/bulk-restore/', events_views.EventBulkRestoreView.as_view(), name='event-bulk-restore'),
    path('events/bulk-hard-delete/', events_views.EventBulkHardDeleteView.as_view(), name='event-bulk-hard-delete'),
    
    # Hard Delete
    path('events/<int:id>/hard-delete/', events_views.EventHardDeleteView.as_view(), name='event-hard-delete'),


       # ============ PUBLICATIONS URLs ============
    # Basic CRUD
    path('publications/', publications_views.PublicationListCreateView.as_view(), name='publication-list-create'),
    path('publications/<int:id>/', publications_views.PublicationRetrieveUpdateDeleteView.as_view(), name='publication-detail'),
    
    # Deleted Publications
    path('publications/deleted/', publications_views.PublicationDeletedListView.as_view(), name='publication-deleted-list'),
    
    # Get Publications by Post
    path('publications/by-post/<int:post_id>/', publications_views.PublicationsByPostView.as_view(), name='publications-by-post'),
    
    # Restore
    path('publications/<int:id>/restore/', publications_views.PublicationRestoreView.as_view(), name='publication-restore'),
    
    # Bulk Operations
    path('publications/bulk-delete/', publications_views.PublicationBulkDeleteView.as_view(), name='publication-bulk-delete'),
    path('publications/bulk-restore/', publications_views.PublicationBulkRestoreView.as_view(), name='publication-bulk-restore'),
    path('publications/bulk-hard-delete/', publications_views.PublicationBulkHardDeleteView.as_view(), name='publication-bulk-hard-delete'),
    
    # Hard Delete
    path('publications/<int:id>/hard-delete/', publications_views.PublicationHardDeleteView.as_view(), name='publication-hard-delete'),
]
