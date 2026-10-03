"""Rotas versionadas: montadas em /api/<version>/ (URLPathVersioning)."""

from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.user.urls.auth")),
    path("users/", include("apps.user.urls.users")),
    path("profiles/", include("apps.user.urls.profiles")),
    path("permissions/", include("apps.user.urls.permissions")),
    path("logs/", include("apps.audit_log.urls")),
    path("public/", include("apps.reputation.urls.public")),
    path("blacklist/", include("apps.reputation.urls.blacklist")),
    path("reports/", include("apps.reputation.urls.reports")),
]
