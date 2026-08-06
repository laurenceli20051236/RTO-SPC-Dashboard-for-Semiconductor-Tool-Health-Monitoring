from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_public_repository_excludes_legacy_and_internal_only_files() -> None:
    excluded_paths = [
        "GITHUB_UPLOAD_MANIFEST.md",
        "configs/pm_deferral_default.yaml",
        "docs/chatgpt_review_package.md",
        "docs/interview_guide.md",
        "docs/interview_talking_points.md",
        "docs/methodology_summary.md",
        "notebooks/06_full_pipeline_demo.ipynb",
        "scripts/create_github_export.py",
        "scripts/create_review_bundle.py",
    ]

    present = [path for path in excluded_paths if (ROOT_DIR / path).exists()]
    legacy_sources = list((ROOT_DIR / "src" / "rta_optimizer").glob("*.py"))
    assert present == []
    assert legacy_sources == []
