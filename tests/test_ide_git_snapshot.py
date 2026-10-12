import subprocess

from pynix_gui.ide_git_snapshot import read_git_snapshot
from pynix_gui.ide_workspace_preview import attach_git_snapshot


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_real_git_branch_status_and_history(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "PYNIX Test")
    git(tmp_path, "config", "user.email", "pynix@example.invalid")
    (tmp_path / "main.pnx").write_text("first", encoding="utf-8")
    git(tmp_path, "add", "main.pnx")
    git(tmp_path, "commit", "-qm", "Initial project")
    (tmp_path / "main.pnx").write_text("updated", encoding="utf-8")
    (tmp_path / "new file.pnx").write_text("untracked", encoding="utf-8")
    snapshot = read_git_snapshot(tmp_path)
    assert snapshot.available
    assert snapshot.branch
    assert any(c.path == "main.pnx" and "M" in c.status for c in snapshot.changes)
    assert any(c.path == "new file.pnx" and c.status == "??" for c in snapshot.changes)
    assert any("Initial project" in h for h in snapshot.history)
    output = attach_git_snapshot('<html><body class="workspace-mode"></body></html>', snapshot)
    assert "Initial project" in output
    assert "new file.pnx" in output
    assert "no Git command will run" in output


def test_non_repo_does_not_show_fake_git_changes(tmp_path):
    snapshot = read_git_snapshot(tmp_path)
    assert not snapshot.available
    assert not snapshot.changes
    source = "<body>original</body>"
    assert attach_git_snapshot(source, snapshot) == source


def test_git_message_is_script_safe(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "PYNIX Test")
    git(tmp_path, "config", "user.email", "pynix@example.invalid")
    (tmp_path / "main.pnx").write_text("hello")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "</script><script>alert(1)</script>")
    result = attach_git_snapshot("<body></body>", read_git_snapshot(tmp_path))
    assert "</script><script>alert(1)</script>" not in result
    assert "\\u003c/script" in result
