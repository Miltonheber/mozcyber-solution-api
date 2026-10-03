from django.urls import path

from apps.education.views import PublicPostDetailView, PublicPostListView

urlpatterns = [
    path("posts/", PublicPostListView.as_view(), name="public-post-list"),
    path("posts/<slug:slug>/", PublicPostDetailView.as_view(), name="public-post-detail"),
]
