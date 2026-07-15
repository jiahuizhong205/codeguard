from __future__ import annotations
import re
from pathlib import Path
from typing import Callable, Awaitable
from codeguard.agent.llm_client import LLMClient
from codeguard.agent.action import parse_action
from codeguard.models.entities import (
    Action, Message, MessageRole, StepEvent, StepType,
    GuardrailLevel, ToolResult,
)
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.governance.guardrail import GuardrailEngine
from codeguard.governance.hitl import HITLManager
from codeguard.governance.audit_log import AuditLog
from codeguard.governance.scope_fence import ScopeFence
from codeguard.feedback.validators import TestValidator
from codeguard.memory.store import MemoryStore
from codeguard.skills.loader import SkillLoader

_CODEBLOCK_RE = re.compile(
    r"```([a-zA-Z0-9+#]*)\s*(?::\s*([^\n]+))?\n(.*?)```",
    re.DOTALL,
)


def extract_code_blocks(text: str) -> list[dict]:
    """Only extract code blocks that have an explicit filename (```lang:filename).

    Blocks without a filename (e.g. ```sh, ```python) are just conversation snippets,
    not downloadable files.
    """
    blocks: list[dict] = []
    for m in _CODEBLOCK_RE.finditer(text):
        lang = m.group(1).lower().strip()
        filename_hint = (m.group(2) or "").strip()
        code = m.group(3)

        if not filename_hint:
            continue

        filename = Path(filename_hint).name
        blocks.append({
            "filename": filename,
            "content": code,
            "size": len(code),
            "language": lang or "text",
        })
    return blocks


class AgentLoop:
    def __init__(
        self,
        llm_client: LLMClient,
        tool_dispatcher: ToolDispatcher,
        guardrail_engine: GuardrailEngine,
        hitl_manager: HITLManager,
        audit_log: AuditLog,
        scope_fence: ScopeFence,
        feedback_validator: TestValidator,
        memory_store: MemoryStore,
        skill_loader: SkillLoader,
        workspace_root: Path,
        max_iterations: int = 20,
    ):
        self._llm = llm_client
        self._dispatcher = tool_dispatcher
        self._guardrail = guardrail_engine
        self._hitl = hitl_manager
        self._audit = audit_log
        self._fence = scope_fence
        self._feedback = feedback_validator
        self._memory = memory_store
        self._skills = skill_loader
        self._workspace = workspace_root
        self._max_iter = max_iterations

    async def run(
        self,
        task: str,
        on_step: Callable[[StepEvent], Awaitable[None]] | None = None,
    ) -> list[StepEvent]:
        steps: list[StepEvent] = []
        step_idx = 0

        async def emit(step: StepEvent):
            steps.append(step)
            if on_step:
                await on_step(step)

        messages: list[Message] = [
            Message(role=MessageRole.SYSTEM, content=(
                "You are a coding agent. Use tools to complete tasks.\n"
                "When creating a file for the user, use write_file tool, "
                "or include the filename in the code block like: ```c:hello.c"
            )),
            Message(role=MessageRole.USER, content=task),
        ]

        for iteration in range(self._max_iter):
            response = await self._llm.call(messages)
            messages.append(Message(role=MessageRole.ASSISTANT, content=response.content))

            await emit(StepEvent(
                step_index=step_idx, step_type=StepType.THINK, content=response.content
            ))
            step_idx += 1

            for block in extract_code_blocks(response.content):
                await emit(StepEvent(
                    step_index=step_idx, step_type=StepType.FILE_OUTPUT,
                    content={"filename": block["filename"], "content": block["content"], "size": block["size"]}
                ))
                step_idx += 1

            action = parse_action(response)
            if action is None:
                await emit(StepEvent(
                    step_index=step_idx, step_type=StepType.RESULT,
                    content="Agent completed (no more actions)"
                ))
                break
            step_idx += 1

            decision = self._guardrail.check(action)
            await emit(StepEvent(
                step_index=step_idx, step_type=StepType.GUARDRAIL,
                content={"level": decision.level.value, "reason": decision.reason, "rule_id": decision.rule_id}
            ))
            step_idx += 1

            if decision.level == GuardrailLevel.DENY:
                messages.append(Message(
                    role=MessageRole.SYSTEM,
                    content=f"Action denied: {decision.reason}",
                ))
                continue

            if decision.level == GuardrailLevel.ASK:
                req = self._hitl.create_request(action)
                await emit(StepEvent(
                    step_index=step_idx, step_type=StepType.HITL,
                    content={"request_id": req.id, "action": action.name}
                ))
                step_idx += 1
                self._hitl.resolve(req.id, "approve")

            result = self._dispatcher.dispatch(action)
            self._audit.record(action, decision, result)

            await emit(StepEvent(
                step_index=step_idx, step_type=StepType.TOOL_CALL,
                content={"tool": action.name, "success": result.success, "output": result.output[:200] if result.output else ""}
            ))
            step_idx += 1

            if action.name == "write_file" and result.success:
                file_path = action.params.get("path", "unknown")
                file_content = action.params.get("content", "")
                await emit(StepEvent(
                    step_index=step_idx, step_type=StepType.FILE_OUTPUT,
                    content={"filename": file_path, "content": file_content, "size": len(file_content)}
                ))
                step_idx += 1

            if action.name in ("run_tests", "run_lint"):
                feedback = self._feedback.validate(result)
                await emit(StepEvent(
                    step_index=step_idx, step_type=StepType.FEEDBACK,
                    content=feedback.to_message()
                ))
                step_idx += 1
                messages.append(Message(
                    role=MessageRole.SYSTEM,
                    content=feedback.to_message(),
                ))
                if feedback.success:
                    await emit(StepEvent(
                        step_index=step_idx, step_type=StepType.RESULT,
                        content="Tests passed — task complete"
                    ))
                    break
            else:
                messages.append(Message(
                    role=MessageRole.SYSTEM,
                    content=f"Tool result: {result.output[:500] if result.output else result.error}",
                ))

        self._memory.save("last_task", "session", task)
        return steps
