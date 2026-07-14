from codeguard.tools.test_tools import RunTests, RunLint


def test_run_tests_pass(tmp_path):
    (tmp_path / "test_pass.py").write_text("def test_ok():\n    assert True\n")
    tool = RunTests()
    result = tool.execute({"command": f"python -m pytest {tmp_path}/test_pass.py -q"})
    assert result.success is True


def test_run_tests_fail(tmp_path):
    (tmp_path / "test_fail.py").write_text("def test_bad():\n    assert False\n")
    tool = RunTests()
    result = tool.execute({"command": f"python -m pytest {tmp_path}/test_fail.py -q"})
    assert result.success is False


def test_run_lint():
    tool = RunLint()
    result = tool.execute({"command": "echo 'lint output'"})
    assert result.success is True
