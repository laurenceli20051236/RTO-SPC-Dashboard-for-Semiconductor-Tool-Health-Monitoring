from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_step6_required_documentation_files_exist() -> None:
    required = [
        "docs/portfolio_case_study.md",
        "docs/architecture_overview.md",
        "docs/methodology_summary.md",
        "docs/interview_talking_points.md",
        "docs/recruiter_quick_start.md",
        "docs/project_limitations.md",
        "docs/release_checklist.md",
        "docs/demo_script.md",
        "docs/chatgpt_review_package.md",
        "docs/screenshots/README.md",
    ]
    missing = [path for path in required if not (ROOT_DIR / path).exists()]
    assert missing == []


def test_step6_screenshot_placeholders_exist() -> None:
    required = [
        "01_tool_health_summary.png.placeholder",
        "02_thickness_monitor.png.placeholder",
        "03_particle_alerts.png.placeholder",
        "04_excursion_review.png.placeholder",
    ]
    screenshot_dir = ROOT_DIR / "docs" / "screenshots"
    missing = [name for name in required if not (screenshot_dir / name).exists()]
    assert missing == []
