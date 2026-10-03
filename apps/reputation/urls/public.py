from django.urls import path

from apps.reputation.views import (
    PublicClassifyView,
    PublicHallOfFameView,
    PublicNumberReputationView,
    PublicReportView,
)

urlpatterns = [
    path("classify/", PublicClassifyView.as_view(), name="public-classify"),
    path("reports/", PublicReportView.as_view(), name="public-report"),
    path("hall-of-fame/", PublicHallOfFameView.as_view(), name="public-hall-of-fame"),
    path("numbers/<str:phone>/", PublicNumberReputationView.as_view(), name="public-number"),
]
