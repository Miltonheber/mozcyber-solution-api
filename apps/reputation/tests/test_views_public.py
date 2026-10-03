import pytest
from django.urls import reverse
from rest_framework.throttling import ScopedRateThrottle

from apps.core.testing.helpers import assert_error
from apps.reputation.models import MessageClassification, NumberReport, PhoneNumber

pytestmark = pytest.mark.django_db

FRAUD_MSG = "Parabéns, ganhou um prémio! Envie o seu PIN M-Pesa em http://x.co"


def url(name, **kw):
    return reverse(name, kwargs={"version": "v1", **kw})


def test_classify_is_public_and_feeds_blacklist(api_client):
    response = api_client.post(
        url("public-classify"), {"phone": "84 123 4567", "message": FRAUD_MSG}, format="json"
    )
    assert response.status_code == 200, response.content
    assert response.data["verdict"] == "fraud"
    assert response.data["reputation"]["number"] == "+258841234567"
    assert response.data["reputation"]["status"] == "blacklisted"
    assert MessageClassification.objects.count() == 1
    assert PhoneNumber.objects.get().classification_count == 1


def test_classify_safe_message_does_not_flag(api_client):
    response = api_client.post(
        url("public-classify"), {"phone": "841234567", "message": "Bom dia"}, format="json"
    )
    assert response.data["verdict"] == "safe" and response.data["reputation"]["status"] == "unknown"


@pytest.mark.parametrize(
    "body", [{}, {"phone": "abc", "message": "x"}, {"phone": "841234567", "message": ""}]
)
def test_classify_validation(api_client, body):
    assert_error(api_client.post(url("public-classify"), body, format="json"), 400, "validation_error")


def test_report_is_public_and_anonymous(api_client):
    body = {"phone": "+258 84 111 2222", "behavior": "Pediu o PIN", "category": "phishing", "channel": "sms"}
    response = api_client.post(url("public-report"), body, format="json")
    assert response.status_code == 201, response.content
    assert set(response.data) == {
        "id",
        "number",
        "category",
        "status",
        "created_at",
    }  # sem dados do denunciante
    report = NumberReport.objects.get()
    assert report.created_by is None and report.phone_number.number == "+258841112222"
    assert PhoneNumber.objects.get().status == "suspicious"


def test_report_validation(api_client):
    assert_error(api_client.post(url("public-report"), {"phone": "841234567"}, format="json"), 400)


def test_number_reputation_known_unknown_invalid(api_client):
    api_client.post(url("public-report"), {"phone": "841234567", "behavior": "x"}, format="json")
    known = api_client.get(url("public-number", phone="+258841234567"))
    assert known.status_code == 200 and known.data["status"] == "suspicious"
    unknown = api_client.get(url("public-number", phone="849999999"))
    assert unknown.status_code == 200 and unknown.data["status"] == "unknown"
    assert not PhoneNumber.objects.filter(number="+258849999999").exists()  # leitura não grava
    assert_error(api_client.get(url("public-number", phone="abc")), 400, "validation_error")


def test_public_endpoints_are_throttled(api_client, monkeypatch):
    monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "public_classify", "2/min")
    body = {"phone": "841234567", "message": "oi"}
    assert api_client.post(url("public-classify"), body, format="json").status_code == 200
    assert api_client.post(url("public-classify"), body, format="json").status_code == 200
    assert_error(api_client.post(url("public-classify"), body, format="json"), 429, "throttled")


def _blacklisted(number, score, reports=0, category="phishing"):
    from apps.reputation.tests.factories import PhoneNumberFactory

    return PhoneNumberFactory(
        number=number, status="blacklisted", risk_score=score, report_count=reports, category=category
    )


def test_hall_of_fame_is_public_blacklisted_only_and_ordered(api_client):
    from apps.reputation.tests.factories import PhoneNumberFactory

    _blacklisted("+258840000001", 80, reports=3)
    _blacklisted("+258840000002", 100, reports=1)
    _blacklisted("+258840000003", 80, reports=5)
    PhoneNumberFactory(number="+258840000004", status="suspicious", risk_score=99)
    PhoneNumberFactory(number="+258840000005", status="cleared", risk_score=0)

    response = api_client.get(url("public-hall-of-fame"))
    assert response.status_code == 200
    assert [n["number"] for n in response.data["results"]] == [
        "+258840000002",
        "+258840000003",
        "+258840000001",
    ]
    assert set(response.data["results"][0]) == {
        "number",
        "status",
        "category",
        "risk_score",
        "report_count",
        "blacklisted_at",
    }


def test_hall_of_fame_filters_by_category_ignores_search_and_paginates(api_client):
    _blacklisted("+258840000001", 90, category="phishing")
    _blacklisted("+258840000002", 80, category="sim_swap")
    _blacklisted("+258840000003", 70, category="sim_swap")

    sim = api_client.get(url("public-hall-of-fame"), {"category": "sim_swap"})
    assert sim.data["count"] == 2
    assert api_client.get(url("public-hall-of-fame"), {"search": "nada"}).data["count"] == 3
    page = api_client.get(url("public-hall-of-fame"), {"size": 2})
    assert len(page.data["results"]) == 2 and page.data["next"]


def test_hall_of_fame_drops_cleared_numbers(auth_client, api_client):
    phone = _blacklisted("+258840000001", 90)
    auth_client(["blacklist:update"]).patch(
        reverse("blacklist-detail", kwargs={"version": "v1", "pk": phone.pk}),
        {"status": "cleared"},
        format="json",
    )
    assert api_client.get(url("public-hall-of-fame")).data["count"] == 0


def test_hall_of_fame_has_constant_queries(api_client, django_assert_max_num_queries):
    for i in range(8):
        _blacklisted(f"+25884100000{i}", 50 + i, reports=i)
    with django_assert_max_num_queries(3):
        assert api_client.get(url("public-hall-of-fame")).data["count"] == 8


def test_hall_of_fame_is_throttled(api_client, monkeypatch):
    monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "public_read", "1/min")
    assert api_client.get(url("public-hall-of-fame")).status_code == 200
    assert_error(api_client.get(url("public-hall-of-fame")), 429, "throttled")
