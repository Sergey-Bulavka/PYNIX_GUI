"""Regression tests for native Git Log and read-only Git metadata bridge."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

from pynix_gui.ide_git_log import (
    GitLogError, read_git_commit, read_git_diff, read_git_log,
)
from pynix_gui.ide_git_window import (
    GIT_WINDOW_STYLE, GIT_WINDOW_SCRIPT, apply_git_window,
)
from pynix_gui.ide_edge_profile import EDGE_PROFILE_SCRIPT, EXISTING_ACTIONS
from pynix_gui.ide_terminal_dock import TERMINAL_DOCK_JS


def git(root, *args):
    return subprocess.run(
        ["git","-C",str(root),*args],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,
    ).stdout.decode("utf-8","replace").strip()


def repo(tmp_path):
    git(tmp_path,"init","-q")
    git(tmp_path,"config","user.name","PYNIX Git Test")
    git(tmp_path,"config","user.email","git@example.invalid")
    (tmp_path/"main.pnx").write_text("first\n",encoding="utf-8")
    git(tmp_path,"add","main.pnx")
    git(tmp_path,"commit","-qm","Initial PYNIX project")
    (tmp_path/"main.pnx").write_text("first\nsecond\n",encoding="utf-8")
    git(tmp_path,"add","main.pnx")
    git(tmp_path,"commit","-qm","Update PYNIX source")
    git(tmp_path,"branch","feature/read-only")
    return tmp_path


def test_real_branches_commits_worktrees_and_filtering(tmp_path):
    root=repo(tmp_path)
    result=read_git_log(root)
    assert result["available"]
    assert result["branch"]==git(root,"branch","--show-current")
    assert result["commits"][0]["subject"]=="Update PYNIX source"
    assert result["commits"][0]["sha"]==git(root,"rev-parse","HEAD")
    assert result["commits"][0]["parents"]
    assert any(r["name"]=="feature/read-only" for r in result["refs"])
    assert any(r["kind"]=="local" for r in result["refs"])
    assert result["worktrees"] and result["worktrees"][0]["path"]
    assert len(read_git_log(root,text="Update PYNIX")["commits"])==1
    assert len(read_git_log(root,user="PYNIX Git Test")["commits"])==2
    ref="refs/heads/feature/read-only"
    assert len(read_git_log(root,branch=ref)["commits"])==2
    assert len(read_git_log(root,path="main.pnx")["commits"])==2
    assert not read_git_log(root,path="unknown.pnx")["commits"]
    full_sha=git(root,"rev-parse","HEAD")
    assert [c["sha"] for c in read_git_log(root,text=full_sha)["commits"]]==[full_sha]


def test_selected_commit_files_and_safe_unified_diff(tmp_path):
    root=repo(tmp_path)
    sha=git(root,"rev-parse","HEAD")
    entry=read_git_commit(root,sha)
    assert entry["sha"]==sha
    assert entry["author"]=="PYNIX Git Test"
    assert any(f["path"]=="main.pnx" for f in entry["files"])
    patch=read_git_diff(root,sha,"main.pnx")
    assert patch["sha"]==sha
    assert patch["path"]=="main.pnx"
    assert "+second" in patch["diff"]


def test_untrusted_git_revisions_and_paths_are_rejected(tmp_path):
    root=repo(tmp_path)
    sha=git(root,"rev-parse","HEAD")
    for invalid in ["HEAD~1","--help","",sha+"^"]:
        with pytest.raises(GitLogError):
            read_git_commit(root,invalid)
    for bad in ["/etc/passwd","../outside","-x",".\\..\\outside"]:
        with pytest.raises(GitLogError):
            read_git_diff(root,sha,bad)
    with pytest.raises(GitLogError):
        read_git_diff(root,sha,"not-in-commit.pnx")
    with pytest.raises(GitLogError):
        read_git_log(root,branch="--all")
    with pytest.raises(GitLogError):
        read_git_log(root,branch="HEAD~1")
    with pytest.raises(GitLogError):
        read_git_log(root,since="today;rm -rf .")
    with pytest.raises(GitLogError):
        read_git_log(root,path="../outside")


def test_not_git_root_and_missing_repo_do_not_read_parent(tmp_path):
    root=repo(tmp_path)
    child=root/"child"
    child.mkdir()
    with pytest.raises(GitLogError,match="root"):
        read_git_log(child)
    unrelated=root.parent/"empty"
    unrelated.mkdir(exist_ok=True)
    with pytest.raises(GitLogError):
        read_git_log(unrelated)


def test_new_git_tool_is_independent_of_legacy_project_rail():
    assert EXISTING_ACTIONS["Git"]=="git-window"
    assert "window.pynixTerminalDock?.toggleGit?.();" in EDGE_PROFILE_SCRIPT
    assert "entry.action==='git-window'" in EDGE_PROFILE_SCRIPT
    assert "const showGit=()=>{" in TERMINAL_DOCK_JS
    assert "const toggleGit=()=>{" in TERMINAL_DOCK_JS
    assert "activateToolView('GIT');" in TERMINAL_DOCK_JS
    assert "showGit,toggleGit" in TERMINAL_DOCK_JS
    assert "pynix-git-active" in GIT_WINDOW_STYLE
    assert ".workspace-mode.pynix-iconless .pynix-git-graph svg" in GIT_WINDOW_STYLE
    assert "const graphLayouts=commits=>" in GIT_WINDOW_SCRIPT
    assert "const savedTabFilters=new Map" in GIT_WINDOW_SCRIPT
    assert "const lastRequests={};" in GIT_WINDOW_SCRIPT
    assert "const searchBox=input=>" in GIT_WINDOW_SCRIPT
    assert "main.replaceChildren(sideRail,branchPane,commitPane,right)" in GIT_WINDOW_SCRIPT
    assert "filesTitle.hidden=!chosen;" in GIT_WINDOW_SCRIPT
    assert "detailsTitle.hidden=!chosen;" in GIT_WINDOW_SCRIPT
    assert "const railAction=(label,iconName,callback)=>" in GIT_WINDOW_SCRIPT
    assert ".pynix-git-right-title[hidden]{display:none!important}" in GIT_WINDOW_STYLE
    assert ".pynix-git-search-wrap:focus-within" in GIT_WINDOW_STYLE
    assert "window.pynixGitLogResult=receive;" in GIT_WINDOW_SCRIPT
    assert "new CustomEvent('pynix:terminal-change'" in TERMINAL_DOCK_JS


def test_log_ui_actions_operate_on_native_snapshots_and_escape_git_text(tmp_path):
    source="<html><body class='workspace-mode'></body></html>"
    output=apply_git_window(source)
    assert 'id="pynix-git-window-controller"' in output
    assert apply_git_window(output)==output
    assert "__PYNIX_GIT_ICONS__" not in output
    assert "general/moreVertical" in output
    # The catalog must embed real licensed SVGs, not merely reference their keys.
    assert r"\u003csvg" in output
    for name in ("general/search","general/add","general/refresh",
                 "nodes/folder","nodes/tag","general/chevronDown",
                 "general/collapseAll","general/expandAll"):
        assert '"'+name+'"' in output
    with pytest.raises(ValueError):
        apply_git_window("<html></html>")
    markers=[
        "const logTabs=['Log']","'Worktrees'","'Branch'","'User'",
        "'Date'","'Paths'","'Text or hash'","Branch or tag",
        "New Git Log tab","Close Worktrees tab","refresh","read-only",
        "pynixGitLog","button('↻',refresh)","renderBranches","renderCommits",
        "renderWorktrees","read-only","read_git",
        "pre.textContent=packet.data.error||packet.data.diff",
        "detailsText.textContent=String(packet.error)",
    ]
    for marker in markers:
        if marker=="read_git":
            continue
        assert marker in output,marker
    assert "innerHTML=commit.subject" not in output
    assert "innerHTML=packet.data.diff" not in output
    node=shutil.which("node")
    if node:
        js=GIT_WINDOW_SCRIPT.split('<script id="pynix-git-window-controller">',1)[1].split("</script>",1)[0]
        path=tmp_path/"git-window.js"
        path.write_text(js,encoding="utf-8")
        p=subprocess.run([node,"--check",str(path)],capture_output=True,
                         text=True,timeout=20)
        assert p.returncode==0,p.stderr


def test_native_registers_read_only_git_handler():
    native=(Path(__file__).parents[1]/"examples"/"ide_native_v4.py").read_text()
    assert "class GitLogHandler(NSObject):" in native
    assert 'pynixGitLog")' in native
    assert "result = read_git_log(" in native
    assert "session.root, branch=filters.get(" in native
    assert "read_git_diff(session.root" in native
    assert "run_threading.Thread(target=worker, daemon=True).start()" in native
    assert "document = apply_git_window(document)" in native
