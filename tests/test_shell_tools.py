from codeguard.tools.shell_tools import RunShell


def test_run_shell_echo():
    tool = RunShell()
    result = tool.execute({"command": "echo hello"})
    assert result.success is True
    assert "hello" in result.output
    assert result.exit_code == 0


def test_run_shell_failure():
    tool = RunShell()
    result = tool.execute({"command": "exit 1"})
    assert result.success is False
    assert result.exit_code == 1
