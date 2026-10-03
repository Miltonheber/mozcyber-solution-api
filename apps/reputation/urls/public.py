from django.urls import path

from apps.reputation.views import PublicClassifyView, PublicNumberReputationView, PublicReportView

urlpatterns = [
    path("classify/", PublicClassifyView.as_view(), name="public-classify"),
    path("reports/", PublicReportView.as_view(), name="public-report"),
    path("numbers/<str:phone>/", PublicNumberReputationView.as_view(), name="public-number"),
]
