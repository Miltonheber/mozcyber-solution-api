from django.urls import path

from apps.reputation.views import ReportDetailView, ReportListView

urlpatterns = [
    path("", ReportListView.as_view(), name="report-list"),
    path("<uuid:pk>/", ReportDetailView.as_view(), name="report-detail"),
]
