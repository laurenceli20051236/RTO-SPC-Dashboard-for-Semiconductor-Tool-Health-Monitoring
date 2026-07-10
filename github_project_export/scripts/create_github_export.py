from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT_DIR / "reports"
DEFAULT_OUTPUT_DIR = REPORTS_DIR / "github_project_export"
DEFAULT_ZIP_PATH = REPORTS_DIR / "rto_spc_dashboard_github_export.zip"

GITHUB_FILES = [
    ".gitignore",
    "README.md",
    "requirements.txt",
    "pyproject.toml",
]

GITHUB_DIRS = [
    ".github",
    "app",
    "configs",
    "data",
    "docs",
    "notebooks",
    "scripts",
    "src",
    "tests",
]

IGNORE_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".ipynb_checkpoints",
}

IGNORE_SUFFIXES = (
    ".pyc",
    ".pyo",
)


def _inside_root(path: Path) -> bool:
    root = ROOT_DIR.resolve()
    resolved = path.resolve()
    return resolved == root or root in resolved.parents


def _ignore_generated(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name in IGNORE_NAMES or name.endswith(IGNORE_SUFFIXES):
            ignored.add(name)
    return ignored


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
    manifest = output_dir / "GITHUB_UPLOAD_MANIFEST.md"
    manifest.write_text(
        "\n".join(
            [
                "# GitHub Upload Manifest",
                "",
                "Upload the contents of this folder as the GitHub repository root.",
                "",
                "## Included",
                "",
                "* " + "\n* ".join(sorted(copied_items)),
                "",
                "## Not Included",
                "",
                "* `.git/` local repository metadata",
                "* `.agents/` local Codex metadata",
                "* `.pytest_cache/`, `__pycache__/`, and Python bytecode",
                "* `tmp/` local logs",
                "* generated review/export zips under `reports/`",
                "",
                "## Quick Start",
                "",
                "```bash",
                "python -m pip install -r requirements.txt",
                "python scripts/generate_sample_data.py",
                "pytest",
                "streamlit run app/dashboard.py",
                "```",
                "",
                "The included CSV files under `data/` are synthetic demo data only.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def create_github_export(output_dir: Path = DEFAULT_OUTPUT_DIR, zip_path: Path = DEFAULT_ZIP_PATH) -> Path:
    output_dir = output_dir.resolve()
    zip_path = zip_path.resolve()
    if not _inside_root(output_dir) or not _inside_root(zip_path):
        raise ValueError("Export paths must stay inside the project workspace.")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    copied_items: list[str] = []
    for relative_path in GITHUB_FILES:
        copied = _copy_file(relative_path, output_dir)
        if copied:
            copied_items.append(copied)
    for relative_path in GITHUB_DIRS:
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
    bundle_path = create_github_export()
    print(f"GitHub export created: {bundle_path}")
