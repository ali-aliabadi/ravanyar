from pathlib import Path

import pytest
from check_spec_format import goal_numbers, problems

GOALS = goal_numbers("## Goal 1 - Care\n\n## Goal 2 - AI help\n")

FILLED_DATA = """
## Data

- **Stored:** a client's phone number.
- **Encrypted:** phone under the client's data key; blind index for login.
- **Consent:** terms of service v1.
- **Retention:** until the account is deleted; data key shredded.
- **Access:** the client only.
- **Sent outside:** nothing.
"""


def write_spec(tmp_path: Path, front: str, body: str = "") -> Path:
    spec_dir = tmp_path / "SPEC-0001-login"
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text(f"---\n{front}\n---\n{body}")
    return spec_dir


@pytest.mark.unit
def test_complete_spec_passes(tmp_path: Path) -> None:
    front = "id: SPEC-0001\nstatus: draft   # comment\ngoal: 1\ndata: identifying"
    assert problems(write_spec(tmp_path, front, FILLED_DATA), GOALS) == []


@pytest.mark.unit
def test_no_personal_data_needs_no_data_section(tmp_path: Path) -> None:
    front = "id: SPEC-0001\nstatus: draft\ngoal: 2\ndata: none"
    assert problems(write_spec(tmp_path, front), GOALS) == []


@pytest.mark.unit
def test_unknown_goal_and_data_class_fail(tmp_path: Path) -> None:
    front = "id: SPEC-0001\nstatus: draft\ngoal: 9\ndata: secret"
    found = problems(write_spec(tmp_path, front), GOALS)
    assert any("goal must be" in p for p in found)
    assert any("data must be" in p for p in found)


@pytest.mark.unit
def test_template_placeholder_counts_as_empty(tmp_path: Path) -> None:
    front = "id: SPEC-0001\nstatus: draft\ngoal: 1\ndata: clinical"
    body = FILLED_DATA.replace("terms of service v1.", "<which consent, which version>")
    found = problems(write_spec(tmp_path, front, body), GOALS)
    assert found == ["data is clinical: fill in Data / Consent"]


@pytest.mark.unit
def test_clinical_spec_without_data_section_lists_every_field(tmp_path: Path) -> None:
    front = "id: SPEC-0001\nstatus: draft\ngoal: 1\ndata: clinical"
    assert len(problems(write_spec(tmp_path, front), GOALS)) == 6
