from unittest.mock import MagicMock

import pytest

from apps.reputation.constants import NumberStatus, Verdict
from apps.reputation.models import PhoneNumber
from apps.reputation.services import (
    ClassificationResult,
    ClassificationService,
    PhoneNumberService,
    ReportService,
)
from apps.reputation.tests.factories import NumberReportFactory, PhoneNumberFactory


def test_reputation_unknown_number_without_db():
    repo = MagicMock()
    repo.find_by_number.return_value = None
    phone = PhoneNumberService(repository=repo, reports=MagicMock()).reputation("+258841234567")
    assert phone.status == NumberStatus.UNKNOWN and phone.pk is not None and phone._state.adding


def test_classify_feeds_reputation_without_db():
    classifier = MagicMock()
    classifier.classify.return_value = ClassificationResult(
        Verdict.FRAUD, "phishing", 0.9, "pede PIN", "rule_based"
    )
    phones = MagicMock()
    phones.register_activity.return_value = PhoneNumber(number="+258841234567")
    repo = MagicMock()
    result = ClassificationService(repository=repo, phones=phones, classifier=classifier).classify(
        "+258841234567", "msg", ip="1.2.3.4"
    )
    assert result["verdict"] == Verdict.FRAUD and result["reputation"].number == "+258841234567"
    assert repo.create.call_args.kwargs["requester_ip"] == "1.2.3.4"
    assert phones.register_activity.call_args.kwargs["high_confidence_fraud"] is True


@pytest.mark.django_db
def test_three_reports_blacklist_the_number():
    service = ReportService()
    for _ in range(3):
        report = service.report("+258841111111", {"behavior": "pediu PIN", "category": "phishing"})
    phone = report.phone_number
    phone.refresh_from_db()
    assert phone.status == NumberStatus.BLACKLISTED
    assert phone.report_count == 3 and phone.blacklisted_at and phone.last_reported_at


@pytest.mark.django_db
def test_rejecting_report_recounts():
    service = ReportService()
    report = service.report("+258842222222", {"behavior": "x"})
    service.update(report, {"status": "rejected"})
    phone = PhoneNumber.objects.get(number="+258842222222")
    assert phone.report_count == 0


@pytest.mark.django_db
def test_clearing_number_resets_it():
    phone = PhoneNumberFactory(status=NumberStatus.BLACKLISTED, risk_score=80, report_count=3)
    NumberReportFactory.create_batch(3, phone_number=phone)
    cleared = PhoneNumberService().update(phone, {"status": "cleared"})
    assert (cleared.status, cleared.risk_score, cleared.report_count) == ("cleared", 0, 0)
    assert cleared.blacklisted_at is None
    assert phone.reports.exclude(status="rejected").count() == 0
