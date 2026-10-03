import pytest
from django.apps import apps
from django.contrib import admin
from django.urls import reverse

from apps.education.tests.factories import PostFactory
from apps.occurrences.tests.factories import LostDocumentOccurrenceFactory
from apps.reputation.tests.factories import (
    MessageClassificationFactory,
    NumberReportFactory,
    PhoneNumberFactory,
)
from apps.user.models import Profile, User
from apps.user.tests.factories import ProfileFactory

pytestmark = pytest.mark.django_db

PROJECT_APPS = ("user", "audit_log", "reputation", "education", "occurrences")


def project_models():
    return [m for label in PROJECT_APPS for m in apps.get_app_config(label).get_models()]


def admin_url(model, action, *args):
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_{action}", args=args)


def test_every_project_model_is_registered():
    missing = [m.__name__ for m in project_models() if not admin.site.is_registered(m)]
    assert not missing, f"Modelos sem admin: {missing}"


def test_changelist_and_search_load_for_every_model(staff_client):
    for model in project_models():
        for params in ({}, {"q": "x"}):
            response = staff_client.get(admin_url(model, "changelist"), params)
            assert response.status_code == 200, f"{model.__name__} {params}"


def test_add_pages_load_where_allowed(staff_client):
    read_only_or_derived = {"ActionLog", "MessageClassification", "PhoneNumber", "NumberReport"}
    for model in project_models():
        response = staff_client.get(admin_url(model, "add"))
        expected = 403 if model.__name__ in read_only_or_derived else 200
        assert response.status_code == expected, model.__name__


def test_change_pages_load(staff_client):
    objs = [
        staff_client.user,
        ProfileFactory(),
        PhoneNumberFactory(),
        NumberReportFactory(),
        MessageClassificationFactory(),
        PostFactory(),
        LostDocumentOccurrenceFactory(),
    ]
    for obj in objs:
        response = staff_client.get(admin_url(type(obj), "change", obj.pk))
        assert response.status_code == 200, type(obj).__name__


def test_history_models_are_read_only(staff_client):
    from apps.audit_log.tests.factories import ActionLogFactory

    for obj in (ActionLogFactory(), MessageClassificationFactory()):
        model = type(obj)
        assert staff_client.post(admin_url(model, "change", obj.pk), {}).status_code == 403
        assert staff_client.post(admin_url(model, "delete", obj.pk), {"post": "yes"}).status_code == 403


def test_user_created_in_admin_gets_hashed_password_profiles_and_author(staff_client):
    profile = ProfileFactory()
    response = staff_client.post(
        admin_url(User, "add"),
        {
            "email": "novo@example.com",
            "name": "Novo",
            "password1": "Sup3r-Secret-Pass!",
            "password2": "Sup3r-Secret-Pass!",
            "profiles": [profile.pk],
        },
    )
    assert response.status_code == 302, response.content[:500]
    user = User.objects.get(email="novo@example.com")
    assert user.check_password("Sup3r-Secret-Pass!") and user.password != "Sup3r-Secret-Pass!"
    assert list(user.profiles.all()) == [profile]
    assert user.created_by == staff_client.user


def test_profile_admin_saves_permissions_and_author(staff_client):
    from apps.user.tests.factories import PermissionFactory

    perm = PermissionFactory()
    response = staff_client.post(
        admin_url(Profile, "add"),
        {"code": "ops", "name": "Ops", "description": "", "permissions": [perm.pk], "is_active": "on"},
    )
    assert response.status_code == 302, response.content[:500]
    profile = Profile.objects.get(code="ops")
    assert list(profile.permissions.all()) == [perm] and profile.created_by == staff_client.user


def test_post_created_in_admin_sets_slug_published_at_and_author(staff_client):
    from apps.education.models import Post

    response = staff_client.post(
        admin_url(Post, "add"),
        {
            "title": "Guia do admin",
            "slug": "",
            "summary": "",
            "body": "Texto",
            "topic": "scams",
            "status": "published",
            "cover_image_url": "",
            "is_active": "on",
        },
    )
    assert response.status_code == 302, response.content[:500]
    post = Post.objects.get()
    assert post.slug == "guia-do-admin" and post.published_at and post.created_by == staff_client.user


def test_rejecting_report_in_admin_recomputes_reputation(staff_client):
    from apps.reputation.models import NumberReport
    from apps.reputation.services import ReportService

    report = ReportService().report("+258841110000", {"behavior": "x"})
    phone = report.phone_number
    phone.refresh_from_db()
    assert phone.report_count == 1
    response = staff_client.post(
        admin_url(NumberReport, "change", report.pk),
        {"status": "rejected", "moderation_note": "Falsa", "is_active": "on"},
    )
    assert response.status_code == 302, response.content[:500]
    phone.refresh_from_db()
    assert phone.report_count == 0
    assert NumberReport.objects.get().updated_by == staff_client.user


def test_admin_actions_moderate_through_services(staff_client):
    from apps.reputation.models import PhoneNumber

    phone = PhoneNumberFactory(status="blacklisted", risk_score=90, report_count=3)
    NumberReportFactory.create_batch(2, phone_number=phone)
    response = staff_client.post(
        admin_url(PhoneNumber, "changelist"),
        {"action": "mark_cleared", "_selected_action": [phone.pk]},
    )
    assert response.status_code == 302
    phone.refresh_from_db()
    assert (phone.status, phone.risk_score, phone.report_count, phone.blacklisted_at) == (
        "cleared",
        0,
        0,
        None,
    )
    assert phone.reports.exclude(status="rejected").count() == 0


def test_closing_occurrence_in_admin_sets_closed_at(staff_client):
    from apps.occurrences.models import LostDocumentOccurrence

    occ = LostDocumentOccurrenceFactory()
    url = admin_url(LostDocumentOccurrence, "change", occ.pk)
    data = {
        "document_type": occ.document_type,
        "document_number": occ.document_number,
        "owner_name": occ.owner_name,
        "owner_contact": "",
        "lost_at": occ.lost_at.isoformat(),
        "location": occ.location,
        "description": "",
        "status": "closed",
        "station_name": occ.station_name,
        "is_active": "on",
    }
    assert staff_client.post(url, data).status_code == 302
    occ.refresh_from_db()
    assert occ.closed_at is not None
    assert staff_client.post(url, {**data, "status": "open"}).status_code == 302
    occ.refresh_from_db()
    assert occ.closed_at is None


def test_admin_requires_staff(client, user):
    assert client.get(reverse("admin:index")).status_code == 302
    client.force_login(user)  # utilizador normal, não staff
    assert client.get(reverse("admin:index")).status_code == 302
