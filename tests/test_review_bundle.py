from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.create_review_bundle import create_review_bundle


def test_create_review_bundle_includes_review_material(tmp_path: Path) -> None:
    zip_path = create_review_bundle(tmp_path / "bundle", tmp_path / "bundle.zip")

    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    assert "bundle/REVIEW_MANIFEST.md" in names
    assert "bundle/docs/chatgpt_review_package.md" in names
    assert "bundle/app/pages/2_Thickness_Monitor.py" in names
    assert "bundle/data/excursion_events.csv" in names
