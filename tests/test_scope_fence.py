import pytest
from pathlib import Path
from codeguard.governance.scope_fence import ScopeFence


def test_allow_path_inside_workspace(tmp_workspace: Path):
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("src/main.py")
    assert ok is True


def test_deny_absolute_path(tmp_workspace: Path):
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("/etc/passwd")
    assert ok is False
    assert "escapes" in reason.lower()


def test_deny_parent_traversal(tmp_workspace: Path):
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("../../etc/passwd")
    assert ok is False
    assert "escapes" in reason.lower()


def test_deny_symlink_escape(tmp_workspace: Path):
    link = tmp_workspace / "link"
    try:
        link.symlink_to("/etc")
    except OSError:
        pytest.skip("symlink creation not permitted on this platform")
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("link/passwd")
    assert ok is False


def test_allow_nested_path(tmp_workspace: Path):
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("a/b/c/d.py")
    assert ok is True
