import pytest
from django.test import RequestFactory

from apps.audit_log.models import ActionLog
from apps.audit_log.services import LogService
from apps.user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_record_extracts_request_data_and_redacts_payload():
    user = UserFactory()
    request = RequestFactory().post(
        "/api/v1/x/?a=1", HTTP_USER_AGENT="pytest-agent", HTTP_X_FORWARDED_FOR="10.0.0.1, 10.0.0.2"
    )
    LogService().record(
        "thing.create",
        user=user,
        request=request,
        resource_type="thing",
        resource_id=42,
        status_code=201,
        payload={"name": "n", "password": "secret"},
        extra={"k": "v"},
    )
    log = ActionLog.objects.get()
    assert (log.user, log.method, log.path) == (user, "POST", "/api/v1/x/?a=1")
    assert (log.ip_address, log.user_agent) == ("10.0.0.1", "pytest-agent")
    assert log.payload == {"name": "n", "password": "***"}
    assert (log.resource_type, log.resource_id, log.status_code, log.extra) == (
        "thing",
        "42",
        201,
        {"k": "v"},
    )


def test_record_without_request_or_user():
    LogService().record("system.job")
    log = ActionLog.objects.get()
    assert log.user is None and log.method == ""
