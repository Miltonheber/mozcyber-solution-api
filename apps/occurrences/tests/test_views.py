import datetime

import pytest
from django.urls import reverse

from apps.core.testing.helpers import assert_error, assert_paginated
from apps.occurrences.models import LostDocumentOccurrence
from apps.occurrences.tests.factories import LostDocumentOccurrenceFactory
from apps.user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

POLICE = ["occurrence:create", "occurrence:read", "occurrence:update"]
ENTITY = ["occurrence:read"]

BODY = {
    "document_type": "bi",
    "document_number": " 1100123456a ",
    "owner_name": "Ana Macuácua",
    "owner_contact": "84 111 2222",
    "lost_at": "2026-09-30",
    "location": "Mercado Central",
    "station_name": "Esquadra da Polícia Nº 1",
}


def url(name, **kw):
    return reverse(name, kwargs={"version": "v1", **kw})


def test_requires_auth_and_permission(api_client, auth_client):
    occ = LostDocumentOccurrenceFactory()
    for name, kw in [("occurrence-list", {}), ("occurrence-detail", {"pk": occ.pk})]:
        assert_error(api_client.get(url(name, **kw)), 401)
        assert_error(auth_client([]).get(url(name, **kw)), 403)
    entity = auth_client(ENTITY)  # entidade só consulta
    assert_error(entity.post(url("occurrence-list"), BODY, format="json"), 403)
    assert_error(entity.patch(url("occurrence-detail", pk=occ.pk), {"location": "x"}, format="json"), 403)


def test_police_creates_and_entity_reads(auth_client):
    police = auth_client(POLICE)
    created = police.post(url("occurrence-list"), BODY, format="json")
    assert created.status_code == 201, created.content
    data = created.data
    assert data["reference"].startswith("OC-") and data["status"] == "open"
    assert data["document_number"] == "1100123456A"  # normalizado
    assert data["registered_by"] == (police.user.name or police.user.email)
    assert LostDocumentOccurrence.objects.get().created_by == police.user

    entity = auth_client(ENTITY)
    assert_paginated(entity.get(url("occurrence-list")), count=1)
    assert entity.get(url("occurrence-detail", pk=data["id"])).data["reference"] == data["reference"]


def test_validation(auth_client):
    client = auth_client(POLICE)
    assert_error(client.post(url("occurrence-list"), {}, format="json"), 400, "validation_error")
    future = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    response = client.post(url("occurrence-list"), {**BODY, "lost_at": future}, format="json")
    assert_error(response, 400, "validation_error")
    assert "lost_at" in response.data["details"]
    response = client.post(url("occurrence-list"), {**BODY, "status": "closed"}, format="json")
    assert "status" in response.data["details"]
    assert_error(client.post(url("occurrence-list"), {**BODY, "document_type": "x"}, format="json"), 400)


def test_detail_404(auth_client):
    client = auth_client(POLICE)
    assert_error(client.get(url("occurrence-detail", pk="00000000-0000-0000-0000-000000000000")), 404)
    assert_error(
        client.patch(url("occurrence-detail", pk="00000000-0000-0000-0000-000000000000"), {}, format="json"),
        404,
    )


def test_close_and_reopen(auth_client):
    client = auth_client(POLICE)
    occ = LostDocumentOccurrenceFactory()
    detail = url("occurrence-detail", pk=occ.pk)
    closed = client.patch(detail, {"status": "closed"}, format="json")
    assert closed.status_code == 200 and closed.data["closed_at"]
    reopened = client.patch(detail, {"status": "open"}, format="json")
    assert reopened.data["closed_at"] is None
    assert reopened.data["reference"] == occ.reference  # referência imutável


def test_list_filters_search_and_pagination(auth_client):
    LostDocumentOccurrenceFactory.create_batch(3)
    LostDocumentOccurrenceFactory(
        document_type="passport", document_number="P123", owner_name="Rui Sitoe", status="found"
    )
    client = auth_client(ENTITY)
    assert_paginated(client.get(url("occurrence-list")), count=4)
    assert_paginated(client.get(url("occurrence-list"), {"size": 2}), count=4, size=2)
    assert_paginated(client.get(url("occurrence-list"), {"document_type": "passport"}), count=1)
    assert_paginated(client.get(url("occurrence-list"), {"status": "found"}), count=1)
    assert_paginated(client.get(url("occurrence-list"), {"document_number": "P123"}), count=1)
    assert_paginated(client.get(url("occurrence-list"), {"search": "sitoe"}), count=1)


def test_list_has_constant_queries_no_n_plus_1(auth_client, django_assert_max_num_queries):
    for _ in range(10):
        LostDocumentOccurrenceFactory(created_by=UserFactory())
    client = auth_client(ENTITY)
    with django_assert_max_num_queries(3):
        assert_paginated(client.get(url("occurrence-list")), count=10)
