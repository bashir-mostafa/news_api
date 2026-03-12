from django.urls import path
from content.views import tags_views 
from content.views import authors_views 

app_name = 'tags'

urlpatterns = [
    # ============ BASIC CRUD ============
    # GET (list all tags), POST (create new tag)
    path('tags/', tags_views.TagListCreateView.as_view(), name='tag-list-create'),
    
    # GET (detail), PUT (update), PATCH (partial update), DELETE (soft delete)
    path('tags/<int:id>/', tags_views.TagRetrieveUpdateDeleteView.as_view(), name='tag-detail'),
    
    # ============ HARD DELETE ============
    # DELETE (permanent delete - admin only)
    path('tags/<int:id>/hard-delete/', tags_views.TagHardDeleteView.as_view(), name='tag-hard-delete'),
    
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
    
    # ============ RESTORE SOFT DELETED ============
    # POST (restore soft deleted authors)
    path('authors/<int:id>/restore/', authors_views.AuthorRestoreView.as_view(), name='author-restore'),
    
    # ============ BULK OPERATIONS ============
    path('authors/bulk-delete/', authors_views.AuthorBulkDeleteView.as_view(), name='author-bulk-delete'),
    path('authors/bulk-restore/', authors_views.AuthorBulkRestoreView.as_view(), name='author-bulk-restore'),
]