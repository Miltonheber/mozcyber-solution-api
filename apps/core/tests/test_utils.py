import pytest

from apps.core.utils import normalize_phone, redact


def test_redact_masks_sensitive_keys_recursively():
    data = {"email": "a@b.c", "password": "x", "nested": {"token": "t", "ok": 1}, "list": [{"refresh": "r"}]}
    assert redact(data) == {
        "email": "a@b.c",
        "password": "***",
        "nested": {"token": "***", "ok": 1},
        "list": [{"refresh": "***"}],
    }


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("84 123 4567", "+258841234567"),
        ("+258 84-123-4567", "+258841234567"),
        ("00258841234567", "+258841234567"),
        ("(84) 1234567", "+258841234567"),
        ("+27 82 123 4567", "+27821234567"),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "123", "1" * 16])
def test_normalize_phone_invalid(raw):
    with pytest.raises(ValueError):
        normalize_phone(raw)


def test_redact_masks_personal_data_fields():
    data = {"document_number": "123", "owner_contact": "84", "reporter_contact": "x", "owner_name": "Ana"}
    assert redact(data) == {
        "document_number": "***",
        "owner_contact": "***",
        "reporter_contact": "***",
        "owner_name": "Ana",
    }
