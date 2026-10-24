#!/usr/bin/env python3
"""Reject a spec with incomplete front matter or an unfilled Data section. Run by `make spec`.

A spec that stores anything about a person declares `data: identifying` or `data: clinical`
and must then fill in every field of its Data section (AGENTS.md §1.4-§1.5). A field still
holding the template's `<placeholder>` counts as empty.
"""

import re
import sys
from pathlib import Path

STATUSES = {"draft", "approved", "implemented", "superseded"}
DATA_CLASSES = {"none", "identifying", "clinical"}
DATA_FIELDS = ("Stored", "Encrypted", "Consent", "Retention", "Access", "Sent outside")


def front_matter(text: str) -> dict[str, str]:
    block = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not block:
        return {}
    fields = {}
    for line in block.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.split("#")[0].strip()
    return fields


def goal_numbers(goals_md: str) -> set[str]:
    return set(re.findall(r"^## Goal (\d+)\b", goals_md, re.MULTILINE))


def problems(spec_dir: Path, goals: set[str]) -> list[str]:
    spec = spec_dir / "spec.md"
    if not spec.exists():
        return ["no spec.md"]
    text = spec.read_text(encoding="utf-8")
    meta = front_matter(text)
    found = []
    expected_id = spec_dir.name[:9]
    if meta.get("id") != expected_id:
        found.append(f"id must be {expected_id}")
    if meta.get("status") not in STATUSES:
        found.append(f"status must be one of {', '.join(sorted(STATUSES))}")
    if meta.get("goal") not in goals:
        found.append(f"goal must be one of {', '.join(sorted(goals))} in docs/goals.md")
    data = meta.get("data")
    if data not in DATA_CLASSES:
        found.append(f"data must be one of {', '.join(sorted(DATA_CLASSES))}")
    elif data != "none":
        section = re.search(r"^## Data\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
        body = section.group(1) if section else ""
        for field in DATA_FIELDS:
            line = re.search(rf"^- \*\*{field}:\*\*(.*)$", body, re.MULTILINE)
            value = line.group(1).strip() if line else ""
            if not value or "<" in value:
                found.append(f"data is {data}: fill in Data / {field}")
    return found


def main() -> int:
    goals = goal_numbers(Path("docs/goals.md").read_text(encoding="utf-8"))
    specs = sorted(Path("specs").glob("SPEC-*"))
    failures = [f"- {d.name}: {p}" for d in specs for p in problems(d, goals)]
    if failures:
        print("Specs with incomplete front matter or Data section:\n")
        print("\n".join(failures))
        return 1
    print(f"spec format ok ({len(specs)} specs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
