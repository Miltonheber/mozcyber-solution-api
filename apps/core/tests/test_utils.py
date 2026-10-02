from apps.core.utils import redact


def test_redact_masks_sensitive_keys_recursively():
    data = {"email": "a@b.c", "password": "x", "nested": {"token": "t", "ok": 1}, "list": [{"refresh": "r"}]}
    assert redact(data) == {
        "email": "a@b.c",
        "password": "***",
        "nested": {"token": "***", "ok": 1},
        "list": [{"refresh": "***"}],
    }
