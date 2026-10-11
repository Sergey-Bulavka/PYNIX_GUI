"""Source-level checks for V4 visual IDE preview and its Git mock."""
from pathlib import Path

PREVIEW = Path(__file__).resolve().parents[1] / "examples" / "icon_direction_preview.html"

def test_preview_exposes_complete_workspace():
    html = PREVIEW.read_text(encoding="utf-8")
    for label in ("EXPLORER", "SOURCE CONTROL", "COMMIT MESSAGE",
                  "CHANGES", "BRANCHES", "HISTORY", "main.pnx"):
        assert label in html

def test_git_panel_is_explicitly_visual_only():
    html = PREVIEW.read_text(encoding="utf-8")
    assert "no Git command will run" in html
    assert "git-commit-btn" in html
    assert "git-branch-title" in html

def test_activity_rail_is_accessible():
    html = PREVIEW.read_text(encoding="utf-8")
    assert "aria-label" in html
    assert "keydown" in html
    assert "Source Control" in html
    assert "git-branch" in html

def test_upstream_assets_and_git_operations_are_present():
    html = PREVIEW.read_text(encoding="utf-8")
    for label in ("GitHub Primer Octicons", "Pull Request", "Commit", "Merge",
                  "Push", "Pull", "History", "Compare"):
        assert label in html
