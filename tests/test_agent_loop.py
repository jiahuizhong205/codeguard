import pytest
from pathlib import Path
from codeguard.agent.loop import AgentLoop
from codeguard.agent.llm_client import MockLLMClient
from codeguard.models.entities import LLMResponse
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.tools.file_tools import WriteFile, ReadFile
from codeguard.governance.guardrail import GuardrailEngine
from codeguard.governance.rules import default_rules
from codeguard.governance.hitl import HITLManager
from codeguard.governance.audit_log import AuditLog
from codeguard.governance.scope_fence import ScopeFence
from codeguard.feedback.validators import TestValidator
from codeguard.memory.store import MemoryStore
from codeguard.skills.loader import SkillLoader


@pytest.fixture
def agent_setup(tmp_workspace: Path):
    dispatcher = ToolDispatcher()
    dispatcher.register(WriteFile(tmp_workspace))
    dispatcher.register(ReadFile(tmp_workspace))

    responses = [
        LLMResponse(
            content="Writing file",
            tool_calls=[{"name": "write_file", "params": {"path": "test.py", "content": "x = 1"}}],
        ),
        LLMResponse(content="Done", tool_calls=[]),
    ]

    loop = AgentLoop(
        llm_client=MockLLMClient(responses),
        tool_dispatcher=dispatcher,
        guardrail_engine=GuardrailEngine(default_rules()),
        hitl_manager=HITLManager(),
        audit_log=AuditLog(tmp_workspace / ".codeguard" / "audit.log"),
        scope_fence=ScopeFence(tmp_workspace),
        feedback_validator=TestValidator(),
        memory_store=MemoryStore(tmp_workspace / ".codeguard" / "memory.json"),
        skill_loader=SkillLoader(tmp_workspace / "skills"),
        workspace_root=tmp_workspace,
    )
    return loop, tmp_workspace


@pytest.mark.asyncio
async def test_agent_loop_executes_action(agent_setup):
    loop, workspace = agent_setup
    steps = await loop.run("Write x=1 to test.py")
    assert len(steps) > 0
    assert (workspace / "test.py").exists()
    assert (workspace / "test.py").read_text() == "x = 1"


@pytest.mark.asyncio
async def test_agent_loop_stops_on_done(agent_setup):
    loop, _ = agent_setup
    steps = await loop.run("Write x=1 to test.py")
    assert steps[-1].step_type.value == "result" or steps[-1].step_type.value == "think"


@pytest.mark.asyncio
async def test_agent_loop_guardrail_blocks_dangerous_action(tmp_workspace: Path):
    dispatcher = ToolDispatcher()
    responses = [
        LLMResponse(
            content="Deleting",
            tool_calls=[{"name": "run_shell", "params": {"command": "rm -rf /"}}],
        ),
        LLMResponse(content="Done", tool_calls=[]),
    ]
    loop = AgentLoop(
        llm_client=MockLLMClient(responses),
        tool_dispatcher=dispatcher,
        guardrail_engine=GuardrailEngine(default_rules()),
        hitl_manager=HITLManager(),
        audit_log=AuditLog(tmp_workspace / ".codeguard" / "audit.log"),
        scope_fence=ScopeFence(tmp_workspace),
        feedback_validator=TestValidator(),
        memory_store=MemoryStore(tmp_workspace / ".codeguard" / "memory.json"),
        skill_loader=SkillLoader(tmp_workspace / "skills"),
        workspace_root=tmp_workspace,
    )
    steps = await loop.run("Delete everything")
    guardrail_steps = [s for s in steps if s.step_type.value == "guardrail"]
    assert len(guardrail_steps) > 0
