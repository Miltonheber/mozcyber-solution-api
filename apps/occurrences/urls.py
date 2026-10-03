from django.urls import path

from apps.occurrences.views import OccurrenceDetailView, OccurrenceListCreateView

urlpatterns = [
    path("", OccurrenceListCreateView.as_view(), name="occurrence-list"),
    path("<uuid:pk>/", OccurrenceDetailView.as_view(), name="occurrence-detail"),
]
