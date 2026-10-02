from django.urls import path

from apps.user.views import ProfileDetailView, ProfileListCreateView

urlpatterns = [
    path("", ProfileListCreateView.as_view(), name="profile-list"),
    path("<uuid:pk>/", ProfileDetailView.as_view(), name="profile-detail"),
]
