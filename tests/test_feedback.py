from codeguard.feedback.validators import TestValidator, LintValidator
from codeguard.models.entities import ToolResult


def test_test_validator_pass():
    output = "1 passed in 0.5s"
    result = ToolResult(success=True, output=output, exit_code=0)
    validator = TestValidator()
    feedback = validator.validate(result)
    assert feedback.success is True
    assert "passed" in feedback.details


def test_test_validator_fail():
    output = "1 failed\n    assert False\n"
    result = ToolResult(success=False, output=output, exit_code=1)
    validator = TestValidator()
    feedback = validator.validate(result)
    assert feedback.success is False
    assert len(feedback.failures) > 0


def test_test_validator_to_message():
    output = "1 passed"
    result = ToolResult(success=True, output=output, exit_code=0)
    validator = TestValidator()
    feedback = validator.validate(result)
    msg = feedback.to_message()
    assert "PASSED" in msg


def test_lint_validator_pass():
    output = "All checks passed"
    result = ToolResult(success=True, output=output, exit_code=0)
    validator = LintValidator()
    feedback = validator.validate(result)
    assert feedback.success is True


def test_lint_validator_fail():
    output = "src/main.py:10: E501 line too long"
    result = ToolResult(success=False, output=output, exit_code=1)
    validator = LintValidator()
    feedback = validator.validate(result)
    assert feedback.success is False
    assert len(feedback.failures) > 0
