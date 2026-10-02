from django.urls import path

from apps.user.views import PermissionDetailView, PermissionListCreateView

urlpatterns = [
    path("", PermissionListCreateView.as_view(), name="permission-list"),
    path("<uuid:pk>/", PermissionDetailView.as_view(), name="permission-detail"),
]
