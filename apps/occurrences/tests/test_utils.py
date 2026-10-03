from apps.occurrences.utils.reference import build_reference, parse_sequence


def test_build_and_parse_reference():
    ref = build_reference(2026, 123)
    assert ref == "OC-2026-000123"
    assert parse_sequence(ref) == 123
