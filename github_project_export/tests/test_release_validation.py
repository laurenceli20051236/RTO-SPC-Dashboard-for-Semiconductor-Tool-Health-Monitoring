from __future__ import annotations

from pathlib import Path

from scripts import validate_release


ROOT_DIR = Path(__file__).resolve().parents[1]
DISCLAIMER = (
    "This project uses fully synthetic and anonymized semiconductor monitor data for public portfolio demonstration only. "
    "It does not contain real tool identifiers, real recipe names, real product information, real wafer records, real lot records, "
    "real process limits, real SPC limits, or any confidential manufacturing information."
)


def test_validate_release_runs_without_crashing() -> None:
    assert validate_release.validate_release() == 0


def test_readme_contains_exact_synthetic_data_disclaimer() -> None:
    readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert DISCLAIMER in readme


def test_forbidden_root_cause_phrases_are_not_present() -> None:
    assert validate_release.check_forbidden_phrases() == []


def test_required_data_files_are_detected() -> None:
    assert validate_release.check_required_data_files() == []


def test_required_docs_are_detected() -> None:
    assert validate_release.check_required_docs() == []
