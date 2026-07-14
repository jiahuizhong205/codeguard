"""Mechanism demo — deterministically reproduces 3 governance behaviors under mock LLM."""
from __future__ import annotations
import asyncio
from pathlib import Path
from codeguard.agent.loop import AgentLoop
from codeguard.agent.llm_client import MockLLMClient
from codeguard.models.entities import LLMResponse
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.tools.file_tools import WriteFile, ReadFile
from codeguard.tools.test_tools import RunTests
from codeguard.governance.guardrail import GuardrailEngine
from codeguard.governance.rules import default_rules
from codeguard.governance.hitl import HITLManager
from codeguard.governance.audit_log import AuditLog
from codeguard.governance.scope_fence import ScopeFence
from codeguard.feedback.validators import TestValidator
from codeguard.memory.store import MemoryStore
from codeguard.skills.loader import SkillLoader


def _make_loop(responses: list[LLMResponse], workspace: Path) -> AgentLoop:
    dispatcher = ToolDispatcher()
    dispatcher.register(WriteFile(workspace))
    dispatcher.register(ReadFile(workspace))
    dispatcher.register(RunTests())
    return AgentLoop(
        llm_client=MockLLMClient(responses),
        tool_dispatcher=dispatcher,
        guardrail_engine=GuardrailEngine(default_rules()),
        hitl_manager=HITLManager(),
        audit_log=AuditLog(workspace / ".codeguard" / "audit.log"),
        scope_fence=ScopeFence(workspace),
        feedback_validator=TestValidator(),
        memory_store=MemoryStore(workspace / ".codeguard" / "memory.json"),
        skill_loader=SkillLoader(workspace / "skills"),
        workspace_root=workspace,
    )


async def demo_1_guardrail_blocks_dangerous_action(tmp_path: Path):
    print("\n=== Demo 1: Guardrail blocks dangerous action ===")
    responses = [
        LLMResponse(
            content="I will delete files",
            tool_calls=[{"name": "run_shell", "params": {"command": "rm -rf /tmp/test"}}],
        ),
        LLMResponse(content="Understood, I won't delete", tool_calls=[]),
    ]
    loop = _make_loop(responses, tmp_path)
    steps = await loop.run("Delete all temp files")
    guardrail_steps = [s for s in steps if s.step_type.value == "guardrail"]
    assert len(guardrail_steps) > 0
    assert guardrail_steps[0].content["level"] == "deny"
    print(f"  Guardrail decision: {guardrail_steps[0].content}")
    print("  PASS: Dangerous action was blocked")


async def demo_2_feedback_loop(tmp_path: Path):
    print("\n=== Demo 2: Feedback loop drives self-correction ===")
    responses = [
        LLMResponse(
            content="Running tests",
            tool_calls=[{"name": "run_tests", "params": {"command": "echo '1 failed' && exit 1"}}],
        ),
        LLMResponse(
            content="I see tests failed, fixing",
            tool_calls=[{"name": "run_tests", "params": {"command": "echo '1 passed' && exit 0"}}],
        ),
    ]
    loop = _make_loop(responses, tmp_path)
    steps = await loop.run("Run tests and fix if needed")
    feedback_steps = [s for s in steps if s.step_type.value == "feedback"]
    assert len(feedback_steps) >= 1
    print(f"  Feedback received: {feedback_steps[0].content[:80]}")
    print("  PASS: Agent received feedback and changed behavior")


async def demo_3_scope_fence(tmp_path: Path):
    print("\n=== Demo 3: Scope fence blocks path escape ===")
    responses = [
        LLMResponse(
            content="Writing outside workspace",
            tool_calls=[{"name": "write_file", "params": {"path": "/etc/passwd", "content": "x"}}],
        ),
        LLMResponse(content="I'll write inside instead", tool_calls=[]),
    ]
    loop = _make_loop(responses, tmp_path)
    steps = await loop.run("Write to system path")
    guardrail_steps = [s for s in steps if s.step_type.value == "guardrail"]
    assert len(guardrail_steps) > 0
    assert guardrail_steps[0].content["level"] == "deny"
    print(f"  Guardrail decision: {guardrail_steps[0].content}")
    print("  PASS: Path escape was blocked")


def run_demo():
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    (tmp / ".codeguard").mkdir(exist_ok=True)
    (tmp / "skills").mkdir(exist_ok=True)

    asyncio.run(demo_1_guardrail_blocks_dangerous_action(tmp))
    asyncio.run(demo_2_feedback_loop(tmp))
    asyncio.run(demo_3_scope_fence(tmp))

    print("\n=== All demos passed ===")
    print(f"Demo workspace: {tmp}")
