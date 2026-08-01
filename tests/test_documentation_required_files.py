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


def test_github_screenshots_are_real_png_files() -> None:
    required = [
        "project_flow.png",
        "dashboard_home.png",
        "tool_health_summary.png",
        "thickness_monitor.png",
        "particle_alerts.png",
        "excursion_review.png",
    ]
    screenshot_dir = ROOT_DIR / "docs" / "screenshots"
    missing = [name for name in required if not (screenshot_dir / name).exists()]
    assert missing == []
    for name in required:
        content = (screenshot_dir / name).read_bytes()
        assert content.startswith(b"\x89PNG\r\n\x1a\n")
        assert len(content) >= 20_000
    assert list(screenshot_dir.glob("*.placeholder")) == []
