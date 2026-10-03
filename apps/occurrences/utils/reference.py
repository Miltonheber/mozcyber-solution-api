def build_reference(year: int, sequence: int) -> str:
    """`OC-2026-000123`."""
    return f"OC-{year}-{sequence:06d}"


def parse_sequence(reference: str) -> int:
    """Sequência de uma referência (`OC-2026-000123` -> 123)."""
    return int(reference.rsplit("-", 1)[1])
