from django.urls import path

from apps.reputation.views import BlacklistDetailView, BlacklistListView

urlpatterns = [
    path("", BlacklistListView.as_view(), name="blacklist-list"),
    path("<uuid:pk>/", BlacklistDetailView.as_view(), name="blacklist-detail"),
]
