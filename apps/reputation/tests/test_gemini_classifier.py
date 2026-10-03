import json
from unittest.mock import MagicMock

import pytest

from apps.reputation.constants import Category, Verdict
from apps.reputation.services.classifier import ClassificationResult
from apps.reputation.services.gemini_classifier import (
    SYSTEM_INSTRUCTION,
    FallbackClassifier,
    GeminiClassifier,
    GeminiError,
)

NUMBER = "+258841234567"


def _client(payload):
    client = MagicMock()
    client.models.generate_content.return_value.text = (
        payload if isinstance(payload, str) else json.dumps(payload)
    )
    return client


def _gemini(payload):
    return GeminiClassifier(client=_client(payload), model="test-model")


def test_valid_response_maps_to_result():
    result = _gemini(
        {
            "verdict": "fraud",
            "category": "sim_swap",
            "confidence": 0.95,
            "explanation": "Pede o código do SIM.",
        }
    ).classify(NUMBER, "Envie o código para trocar o seu SIM")
    assert result.provider == "gemini"
    assert (result.verdict, result.category, result.confidence) == (Verdict.FRAUD, Category.SIM_SWAP, 0.95)
    assert result.raw["model"] == "test-model"


def test_message_is_sent_as_data_with_system_instruction():
    client = _client({"verdict": "safe", "category": None, "confidence": 0.9, "explanation": "ok"})
    GeminiClassifier(client=client, model="m").classify(NUMBER, "olá")
    kwargs = client.models.generate_content.call_args.kwargs
    assert "<mensagem>\nolá\n</mensagem>" in kwargs["contents"]
    assert kwargs["config"].system_instruction == SYSTEM_INSTRUCTION


def test_safe_drops_category_and_confidence_is_clamped():
    result = _gemini(
        {"verdict": "safe", "category": "phishing", "confidence": 3, "explanation": "ok"}
    ).classify(NUMBER, "olá")
    assert result.category is None
    assert result.confidence == 1.0


def test_unknown_category_becomes_other():
    result = _gemini(
        {"verdict": "suspicious", "category": "xpto", "confidence": 0.5, "explanation": "?"}
    ).classify(NUMBER, "x")
    assert result.category == Category.OTHER


@pytest.mark.parametrize(
    "payload",
    [
        "isto não é json",
        [],
        {"verdict": "maybe", "category": None, "confidence": 0.5, "explanation": "x"},
        {"verdict": "fraud", "category": "other", "confidence": "alta", "explanation": "x"},
    ],
)
def test_invalid_response_raises(payload):
    with pytest.raises(GeminiError):
        _gemini(payload).classify(NUMBER, "x")


def test_client_exception_is_wrapped():
    client = MagicMock()
    client.models.generate_content.side_effect = TimeoutError("timeout")
    with pytest.raises(GeminiError):
        GeminiClassifier(client=client, model="m").classify(NUMBER, "x")


def test_prompt_lists_every_category():
    for category in Category.values:
        assert category in SYSTEM_INSTRUCTION


def _ok_result():
    return ClassificationResult(Verdict.FRAUD, Category.PHISHING, 0.9, "ia", "gemini")


def test_fallback_uses_primary_when_it_works():
    primary, fallback = MagicMock(), MagicMock()
    primary.classify.return_value = _ok_result()
    result = FallbackClassifier(primary=primary, fallback=fallback).classify(NUMBER, "x")
    assert result.provider == "gemini"
    fallback.classify.assert_not_called()


def test_fallback_on_primary_failure():
    primary = MagicMock()
    primary.classify.side_effect = GeminiError("quota")
    result = FallbackClassifier(primary=primary).classify(NUMBER, "Ganhou um prémio! Envie o seu PIN")
    assert result.provider == "rule_based"
    assert result.verdict != Verdict.SAFE
    assert result.raw["fallback_reason"] == "quota"


def test_fallback_without_api_key(settings):
    settings.GEMINI_API_KEY = ""
    result = FallbackClassifier().classify(NUMBER, "olá, tudo bem?")
    assert result.provider == "rule_based"
    assert "GEMINI_API_KEY" in result.raw["fallback_reason"]


class _ApiError(Exception):
    def __init__(self, code):
        super().__init__(f"{code} erro")
        self.code = code


def _ok_response():
    response = MagicMock()
    response.text = json.dumps(
        {"verdict": "suspicious", "category": "other", "confidence": 0.6, "explanation": "x"}
    )
    return response


@pytest.fixture
def no_sleep(monkeypatch):
    monkeypatch.setattr("apps.reputation.services.gemini_classifier.time.sleep", lambda s: None)


def test_transient_error_is_retried_once(no_sleep):
    client = MagicMock()
    client.models.generate_content.side_effect = [_ApiError(503), _ok_response()]
    result = GeminiClassifier(client=client, model="m").classify(NUMBER, "x")
    assert result.provider == "gemini" and result.verdict == Verdict.SUSPICIOUS
    assert client.models.generate_content.call_count == 2


def test_gives_up_after_max_attempts(no_sleep):
    client = MagicMock()
    client.models.generate_content.side_effect = _ApiError(503)
    with pytest.raises(GeminiError):
        GeminiClassifier(client=client, model="m").classify(NUMBER, "x")
    assert client.models.generate_content.call_count == 2


def test_non_transient_error_is_not_retried(no_sleep):
    client = MagicMock()
    client.models.generate_content.side_effect = _ApiError(400)
    with pytest.raises(GeminiError):
        GeminiClassifier(client=client, model="m").classify(NUMBER, "x")
    assert client.models.generate_content.call_count == 1


def test_prompt_covers_payment_redirect_pattern():
    assert "em nome de" in SYSTEM_INSTRUCTION and "suspicious" in SYSTEM_INSTRUCTION
