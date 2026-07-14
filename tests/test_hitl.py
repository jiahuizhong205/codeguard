# tests/test_hitl.py
import pytest
from datetime import datetime, timedelta
from codeguard.governance.hitl import HITLManager
from codeguard.models.entities import Action, HITLState


@pytest.fixture
def manager():
    return HITLManager(timeout=60)


def test_create_request(manager):
    action = Action(name="run_shell", params={"command": "git push"})
    req = manager.create_request(action)
    assert req.state == HITLState.PENDING
    assert req.action.name == "run_shell"


def test_approve_request(manager):
    action = Action(name="run_shell", params={"command": "git push"})
    req = manager.create_request(action)
    manager.resolve(req.id, "approve")
    assert req.state == HITLState.APPROVED
    assert req.resolved_at is not None


def test_deny_request(manager):
    action = Action(name="run_shell", params={"command": "git push"})
    req = manager.create_request(action)
    manager.resolve(req.id, "deny")
    assert req.state == HITLState.DENIED


def test_timeout_request():
    mgr = HITLManager(timeout=0)
    action = Action(name="run_shell", params={"command": "git push"})
    req = mgr.create_request(action)
    mgr.check_timeout(req)
    assert req.state == HITLState.TIMEOUT


def test_unknown_request_id(manager):
    with pytest.raises(KeyError):
        manager.resolve("nonexistent-id", "approve")


def test_get_pending_requests(manager):
    action1 = Action(name="run_shell", params={"command": "git push"})
    action2 = Action(name="run_shell", params={"command": "npm publish"})
    req1 = manager.create_request(action1)
    req2 = manager.create_request(action2)
    manager.resolve(req1.id, "approve")
    pending = manager.get_pending()
    assert len(pending) == 1
    assert pending[0].id == req2.id


def test_timeout_only_affects_pending(manager):
    """超时仅影响 PENDING 状态的请求，已审批的不应被超时覆盖。"""
    action = Action(name="run_shell", params={"command": "git push"})
    req = manager.create_request(action)
    manager.resolve(req.id, "approve")
    assert req.state == HITLState.APPROVED
    manager.check_timeout(req)
    assert req.state == HITLState.APPROVED  # 不应被覆盖


def test_resolved_request_has_resolved_at(manager):
    action = Action(name="run_shell", params={"command": "git push"})
    req = manager.create_request(action)
    assert req.resolved_at is None
    manager.resolve(req.id, "approve")
    assert req.resolved_at is not None
