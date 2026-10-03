import pytest
from django.urls import reverse

from apps.core.testing.helpers import assert_error, assert_paginated
from apps.reputation.tests.factories import NumberReportFactory, PhoneNumberFactory

pytestmark = pytest.mark.django_db


def url(name, **kw):
    return reverse(name, kwargs={"version": "v1", **kw})


def test_moderation_requires_auth_and_permission(api_client, auth_client):
    phone = PhoneNumberFactory()
    report = NumberReportFactory()
    for name, kw in [
        ("blacklist-list", {}),
        ("blacklist-detail", {"pk": phone.pk}),
        ("report-list", {}),
        ("report-detail", {"pk": report.pk}),
    ]:
        assert_error(api_client.get(url(name, **kw)), 401)
        assert_error(auth_client([]).get(url(name, **kw)), 403)
    assert_error(
        auth_client(["blacklist:read"]).patch(url("blacklist-detail", pk=phone.pk), {}, format="json"), 403
    )
    assert_error(
        auth_client(["report:read"]).patch(url("report-detail", pk=report.pk), {}, format="json"), 403
    )


def test_blacklist_list_filters_search_and_queries(auth_client, django_assert_max_num_queries):
    PhoneNumberFactory.create_batch(6, status="blacklisted")
    PhoneNumberFactory.create_batch(4)
    client = auth_client(["blacklist:read"])
    with django_assert_max_num_queries(3):
        assert_paginated(client.get(url("blacklist-list")), count=10)
    assert_paginated(client.get(url("blacklist-list"), {"status": "blacklisted"}), count=6)
    target = PhoneNumberFactory(number="+258870000001")
    assert_paginated(client.get(url("blacklist-list"), {"search": "870000001"}), count=1)
    assert client.get(url("blacklist-detail", pk=target.pk)).data["number"] == "+258870000001"


def test_blacklist_detail_404_and_moderate(auth_client):
    client = auth_client(["blacklist:read", "blacklist:update"])
    assert_error(client.get(url("blacklist-detail", pk="00000000-0000-0000-0000-000000000000")), 404)
    phone = PhoneNumberFactory(status="blacklisted", risk_score=90)
    response = client.patch(url("blacklist-detail", pk=phone.pk), {"status": "cleared"}, format="json")
    assert (
        response.status_code == 200
        and response.data["status"] == "cleared"
        and response.data["risk_score"] == 0
    )
    assert_error(client.patch(url("blacklist-detail", pk=phone.pk), {"status": "bad"}, format="json"), 400)


def test_report_list_no_n_plus_1_and_moderation(auth_client, django_assert_max_num_queries):
    phones = PhoneNumberFactory.create_batch(5)
    for p in phones:
        NumberReportFactory.create_batch(2, phone_number=p, status="pending")
    client = auth_client(["report:read", "report:update"])
    with django_assert_max_num_queries(3):
        response = client.get(url("report-list"))
    assert_paginated(response, count=10)
    assert_paginated(client.get(url("report-list"), {"phone_number__number": phones[0].number}), count=2)
    report_id = response.data["results"][0]["id"]
    patched = client.patch(
        url("report-detail", pk=report_id), {"status": "confirmed", "moderation_note": "ok"}, format="json"
    )
    assert patched.status_code == 200 and patched.data["status"] == "confirmed"
