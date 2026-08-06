from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
README_PATH = ROOT_DIR / "README.md"
DOCS_DIR = ROOT_DIR / "docs"
DATA_DIR = ROOT_DIR / "data"

SYNTHETIC_DATA_DISCLAIMER = (
    "This project uses fully synthetic and anonymized semiconductor monitor data for public portfolio demonstration only. "
    "It does not contain real tool identifiers, real recipe names, real product information, real wafer records, real lot records, "
    "real process limits, real SPC limits, or any confidential manufacturing information."
)

REQUIRED_DATA_FILES = [
    "monitor_measurements.csv",
    "spc_results.csv",
    "excursion_events.csv",
]

REQUIRED_DOCS = [
    "portfolio_case_study.md",
    "architecture_overview.md",
    "methodology.md",
    "data_dictionary.md",
    "deployment_guide.md",
    "recruiter_quick_start.md",
    "project_limitations.md",
    "release_checklist.md",
    "demo_script.md",
    "reporting_workflow.md",
    "schema_validation.md",
    "screenshots/README.md",
]

REQUIRED_SCREENSHOTS = [
    "project_flow.png",
    "dashboard_home.png",
    "tool_health_summary.png",
    "thickness_monitor.png",
    "particle_alerts.png",
    "excursion_review.png",
]

FORBIDDEN_PHRASES = [
    "root " + "cause determined",
    "root " + "cause identified automatically",
    "confirmed " + "cause",
    "production disposition",
    "production " + "SPC system",
    "real " + "Intel data",
    "real " + "fab data",
    "real process limits",
]

ALLOWED_NEGATIVE_CONTEXTS = [
    "does not contain real process limits or production disposition rules",
    "does not contain real tool identifiers, real recipe names, real product information, real wafer records, real lot records, real process limits, real spc limits",
    "fully synthetic and anonymized semiconductor monitor data",
    "no production disposition",
    "synthetic demo health score, not a production disposition rule",
    "does not determine root " + "cause automatically",
]


def _pass(message: str) -> None:
    print(f"[PASS] {message}")


def _fail(message: str) -> None:
    print(f"[FAIL] {message}")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_readme_disclaimer() -> list[str]:
    text = _read_text(README_PATH) if README_PATH.exists() else ""
    if SYNTHETIC_DATA_DISCLAIMER not in text:
        return ["README is missing the exact synthetic-data disclaimer"]
    _pass("README contains synthetic-data disclaimer")
    return []


def check_required_data_files() -> list[str]:
    errors: list[str] = []
    for filename in REQUIRED_DATA_FILES:
        path = DATA_DIR / filename
        if not path.exists():
            errors.append(f"missing data file: {filename}")
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            errors.append(f"unable to read data file {filename}: {exc}")
            continue
        if df.empty:
            errors.append(f"data file is empty: {filename}")
    if not errors:
        _pass("Required data files found")
        _pass("Sample data files are non-empty")
    return errors


def check_excursion_events() -> list[str]:
    path = DATA_DIR / "excursion_events.csv"
    if not path.exists():
        return ["excursion_events.csv is missing"]
    df = pd.read_csv(path)
    if "event_id" not in df.columns:
        return ["excursion_events.csv is missing event_id column"]
    _pass("excursion_events.csv exists and has event_id column")
    return []


def check_required_docs() -> list[str]:
    errors = [f"missing documentation file: {doc}" for doc in REQUIRED_DOCS if not (DOCS_DIR / doc).exists()]
    if not errors:
        _pass("Required docs found")
    return errors


def check_required_screenshots() -> list[str]:
    errors: list[str] = []
    screenshot_dir = DOCS_DIR / "screenshots"
    png_signature = b"\x89PNG\r\n\x1a\n"
    for filename in REQUIRED_SCREENSHOTS:
        path = screenshot_dir / filename
        if not path.exists():
            errors.append(f"missing screenshot: {filename}")
            continue
        content = path.read_bytes()
        if not content.startswith(png_signature):
            errors.append(f"screenshot is not a valid PNG: {filename}")
        elif len(content) < 20_000:
            errors.append(f"screenshot is unexpectedly small: {filename}")
    placeholders = sorted(screenshot_dir.glob("*.placeholder"))
    if placeholders:
        errors.append("placeholder screenshots remain: " + ", ".join(path.name for path in placeholders))
    if not errors:
        _pass("Required GitHub screenshots are valid PNG files")
    return errors


def _text_files_to_scan() -> list[Path]:
    paths = [README_PATH]
    paths.extend(DOCS_DIR.glob("*.md"))
    paths.extend((DOCS_DIR / "screenshots").glob("*.md"))
    paths.extend((ROOT_DIR / "app").glob("*.py"))
    paths.extend((ROOT_DIR / "app" / "pages").glob("*.py"))
    return [path for path in paths if path.exists()]


def check_forbidden_phrases() -> list[str]:
    errors: list[str] = []
    for path in _text_files_to_scan():
        text = _read_text(path).lower()
        for phrase in FORBIDDEN_PHRASES:
            phrase_lower = phrase.lower()
            if phrase_lower not in text:
                continue
            if any(allowed in text for allowed in ALLOWED_NEGATIVE_CONTEXTS):
                continue
            errors.append(f"forbidden phrase in {path.relative_to(ROOT_DIR)}: {phrase}")
    if not errors:
        _pass("Forbidden phrases not found")
    return errors


def check_pytest_invocable() -> list[str]:
    pyproject = ROOT_DIR / "pyproject.toml"
    tests_dir = ROOT_DIR / "tests"
    if not pyproject.exists() or not tests_dir.exists():
        return ["pytest cannot be invoked separately because test project metadata or tests folder is missing"]
    _pass("pytest can be invoked separately")
    return []


def validate_release() -> int:
    checks = [
        check_readme_disclaimer,
        check_required_data_files,
        check_excursion_events,
        check_required_docs,
        check_required_screenshots,
        check_forbidden_phrases,
        check_pytest_invocable,
    ]
    errors: list[str] = []
    for check in checks:
        errors.extend(check())

    if errors:
        for error in errors:
            _fail(error)
        print("Release validation failed.")
        return 1

    print("Release validation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(validate_release())
