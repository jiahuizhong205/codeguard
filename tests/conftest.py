import pytest
from pathlib import Path


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Provide a temporary workspace directory."""
    (tmp_path / ".codeguard").mkdir()
    return tmp_path
