import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.reputation.constants import NumberStatus, ReportStatus
from apps.reputation.tests.factories import (
    MessageClassificationFactory,
    NumberReportFactory,
    PhoneNumberFactory,
)

pytestmark = pytest.mark.django_db


def test_phone_number_defaults():
    p = PhoneNumberFactory()
    assert p.status == NumberStatus.UNKNOWN
    assert (p.risk_score, p.report_count, p.classification_count, p.fraud_count) == (0, 0, 0, 0)
    assert p.blacklisted_at is None and p.created_by is None


def test_phone_number_is_unique():
    PhoneNumberFactory(number="+258841234567")
    with pytest.raises(IntegrityError):
        PhoneNumberFactory(number="+258841234567")


def test_risk_score_validator():
    p = PhoneNumberFactory.build(risk_score=101)
    with pytest.raises(ValidationError):
        p.full_clean(exclude=["created_by", "updated_by"])


def test_related_names_and_defaults():
    phone = PhoneNumberFactory()
    MessageClassificationFactory(phone_number=phone)
    report = NumberReportFactory(phone_number=phone)
    assert phone.classifications.count() == 1
    assert list(phone.reports.all()) == [report]
    assert report.status == ReportStatus.PENDING
