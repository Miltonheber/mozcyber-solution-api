from django.urls import path

from apps.education.views import PostDetailView, PostListCreateView

urlpatterns = [
    path("", PostListCreateView.as_view(), name="post-list"),
    path("<uuid:pk>/", PostDetailView.as_view(), name="post-detail"),
]
