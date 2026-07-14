import pytest
from pathlib import Path
from codeguard.tools.file_tools import ReadFile, WriteFile, EditFile, ListFiles, SearchContent


def test_read_file(tmp_workspace: Path):
    (tmp_workspace / "test.py").write_text("print('hello')")
    tool = ReadFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "test.py"})
    assert result.success is True
    assert "hello" in result.output


def test_read_file_not_found(tmp_workspace: Path):
    tool = ReadFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "nonexistent.py"})
    assert result.success is False
    assert "not found" in result.error.lower()


def test_write_file(tmp_workspace: Path):
    tool = WriteFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "output.py", "content": "x = 1"})
    assert result.success is True
    assert (tmp_workspace / "output.py").read_text() == "x = 1"


def test_edit_file(tmp_workspace: Path):
    (tmp_workspace / "test.py").write_text("old code\n")
    tool = EditFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "test.py", "old": "old", "new": "new"})
    assert result.success is True
    assert "new code" in (tmp_workspace / "test.py").read_text()


def test_edit_file_no_match(tmp_workspace: Path):
    (tmp_workspace / "test.py").write_text("hello\n")
    tool = EditFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "test.py", "old": "nonexistent", "new": "x"})
    assert result.success is False


def test_list_files(tmp_workspace: Path):
    (tmp_workspace / "a.py").write_text("")
    (tmp_workspace / "b.py").write_text("")
    (tmp_workspace / "c.txt").write_text("")
    tool = ListFiles(workspace_root=tmp_workspace)
    result = tool.execute({"pattern": "*.py"})
    assert result.success is True
    assert "a.py" in result.output
    assert "b.py" in result.output
    assert "c.txt" not in result.output


def test_search_content(tmp_workspace: Path):
    (tmp_workspace / "test.py").write_text("def foo():\n    return 42\n")
    tool = SearchContent(workspace_root=tmp_workspace)
    result = tool.execute({"pattern": "foo"})
    assert result.success is True
    assert "foo" in result.output
