from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT_DIR / "reports"
DEFAULT_OUTPUT_DIR = REPORTS_DIR / "chatgpt_review_bundle"
DEFAULT_ZIP_PATH = REPORTS_DIR / "chatgpt_review_bundle.zip"

REVIEW_FILES = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "docs/chatgpt_review_package.md",
    "docs/recruiter_quick_start.md",
    "docs/demo_script.md",
    "docs/methodology.md",
    "docs/data_dictionary.md",
    "docs/deployment_guide.md",
    "docs/confidentiality_note.md",
    "data/excursion_events.csv",
    "data/spc_results.csv",
    "data/monitor_measurements.csv",
]

REVIEW_DIRS = [
    "app",
    "src/rto_spc",
    "docs/screenshots",
]


def _ignore_generated(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name == "__pycache__" or name.endswith(".pyc")}


def _copy_file(relative_path: str, output_dir: Path) -> str | None:
    source = ROOT_DIR / relative_path
    if not source.exists():
        return None
    destination = output_dir / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return relative_path


def _copy_dir(relative_path: str, output_dir: Path) -> str | None:
    source = ROOT_DIR / relative_path
    if not source.exists():
        return None
    destination = output_dir / relative_path
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=_ignore_generated)
    return relative_path


def _write_manifest(output_dir: Path, copied_items: list[str]) -> None:
    manifest = output_dir / "REVIEW_MANIFEST.md"
    manifest.write_text(
        "\n".join(
            [
                "# ChatGPT Review Bundle",
                "",
                "This bundle is generated from the local RTO SPC Dashboard repository.",
                "The local Streamlit URL is not externally reachable, so this package provides code, docs, screenshots, and synthetic CSV outputs for review.",
                "",
                "## Recommended Review Order",
                "",
                "1. `README.md`",
                "2. `docs/chatgpt_review_package.md`",
                "3. `app/dashboard.py`",
                "4. `app/pages/2_Thickness_Monitor.py`",
                "5. `app/pages/3_Particle_Alerts.py`",
                "6. `data/excursion_events.csv`",
                "",
                "## Included Items",
                "",
                "* " + "\n* ".join(sorted(copied_items)),
                "",
            ]
        ),
        encoding="utf-8",
    )


def create_review_bundle(output_dir: Path = DEFAULT_OUTPUT_DIR, zip_path: Path = DEFAULT_ZIP_PATH) -> Path:
    output_dir = output_dir.resolve()
    zip_path = zip_path.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    copied_items: list[str] = []
    for relative_path in REVIEW_FILES:
        copied = _copy_file(relative_path, output_dir)
        if copied:
            copied_items.append(copied)
    for relative_path in REVIEW_DIRS:
        copied = _copy_dir(relative_path, output_dir)
        if copied:
            copied_items.append(copied)

    _write_manifest(output_dir, copied_items)

    if zip_path.exists():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(output_dir.parent))
    return zip_path


if __name__ == "__main__":
    bundle_path = create_review_bundle()
    print(f"Review bundle created: {bundle_path}")
