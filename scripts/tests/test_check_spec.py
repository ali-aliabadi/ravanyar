import pytest
from check_spec import is_approved


@pytest.mark.unit
@pytest.mark.parametrize(
    ("status", "approved"),
    [
        ("approved", True),
        ("approved   # draft | approved | implemented | superseded", True),
        ("draft   # draft | approved | implemented | superseded", False),
        ("implemented", False),
    ],
)
def test_is_approved_reads_status_like_the_format_gate(status: str, approved: bool) -> None:
    assert is_approved(f"---\nid: SPEC-0001\nstatus: {status}\n---\n") is approved
