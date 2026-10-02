import pytest
from django.urls import reverse

from apps.audit_log.models import ActionLog
from apps.audit_log.tests.factories import ActionLogFactory
from apps.core.testing.helpers import assert_error, assert_paginated
from apps.user.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db
URL = lambda: reverse("log-list", kwargs={"version": "v1"})  # noqa: E731


def test_requires_permission(auth_client):
    assert_error(auth_client([]).get(URL()), 403)


def test_list_filter_and_pagination(auth_client):
    ActionLogFactory.create_batch(3, action="a.one")
    ActionLogFactory(action="b.two")
    client = auth_client(["log:read"])
    assert_paginated(client.get(URL(), {"action": "a.one", "size": 2}), count=3, size=2)
    assert_paginated(client.get(URL(), {"search": "b."}), count=1)


def test_list_no_n_plus_1(auth_client, django_assert_max_num_queries):
    for _ in range(10):
        ActionLogFactory(user=UserFactory())
    client = auth_client(["log:read"])
    with django_assert_max_num_queries(4):  # auth + count + logs(select_related user)
        assert_paginated(client.get(URL(), {"size": 20}), count=10)


def test_login_and_user_create_are_logged(api_client, auth_client):
    user = UserFactory()
    api_client.post(
        reverse("auth-login", kwargs={"version": "v1"}), {"email": user.email, "password": DEFAULT_PASSWORD}
    )
    login_log = ActionLog.objects.get(action="auth.login")
    assert login_log.payload["password"] == "***" and login_log.status_code == 200

    client = auth_client(["user:create"])
    client.post(
        reverse("user-list", kwargs={"version": "v1"}),
        {"email": "logged@example.com", "password": "Str0ng!Pass99"},
        format="json",
        HTTP_USER_AGENT="agent-x",
    )
    log = ActionLog.objects.get(action="user.create")
    assert log.user == client.user and log.resource_type == "user" and log.resource_id
    assert log.user_agent == "agent-x" and log.payload["password"] == "***"


def test_failed_requests_below_500_are_logged_too(auth_client):
    client = auth_client(["user:create"])
    client.post(reverse("user-list", kwargs={"version": "v1"}), {}, format="json")
    assert ActionLog.objects.get(action="user.create").status_code == 400
