from django.urls import path
from content.views import tags_views 
from content.views import authors_views 
from content.views import categories_views
from content.views import posts_views

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
]