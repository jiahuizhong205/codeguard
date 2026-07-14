import pytest
from pathlib import Path
from codeguard.credentials.manager import CredentialManager


@pytest.fixture
def cred_mgr(tmp_workspace: Path):
    mgr = CredentialManager(tmp_workspace / ".codeguard" / "credentials.enc")
    mgr.unlock("test-master-password")
    return mgr


def test_store_and_get(cred_mgr):
    cred_mgr.store("llm_api_key", "sk-test123")
    value = cred_mgr.get("llm_api_key")
    assert value == "sk-test123"


def test_status_configured(cred_mgr):
    cred_mgr.store("llm_api_key", "sk-test123")
    assert cred_mgr.status("llm_api_key") is True


def test_status_not_configured(cred_mgr):
    assert cred_mgr.status("llm_api_key") is False


def test_clear(cred_mgr):
    cred_mgr.store("llm_api_key", "sk-test123")
    cred_mgr.clear("llm_api_key")
    assert cred_mgr.status("llm_api_key") is False
    assert cred_mgr.get("llm_api_key") is None


def test_update(cred_mgr):
    cred_mgr.store("llm_api_key", "old-key")
    cred_mgr.store("llm_api_key", "new-key")
    assert cred_mgr.get("llm_api_key") == "new-key"


def test_wrong_password_fails(tmp_workspace: Path):
    mgr1 = CredentialManager(tmp_workspace / ".codeguard" / "credentials.enc")
    mgr1.unlock("correct-password")
    mgr1.store("key", "value")

    mgr2 = CredentialManager(tmp_workspace / ".codeguard" / "credentials.enc")
    assert mgr2.unlock("wrong-password") is False
