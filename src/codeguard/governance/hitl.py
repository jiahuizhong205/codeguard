from __future__ import annotations
from datetime import datetime, timedelta
from uuid import uuid4
from codeguard.models.entities import Action, HITLRequest, HITLState


class HITLManager:
    """Human-in-the-loop approval state machine.

    职责范围（按 SPEC_PROCESS.md 决策）：

    审批生命周期（HITLManager 负责）：
      PENDING → APPROVED/DENIED  (resolve)
      PENDING → TIMEOUT          (check_timeout)

    执行生命周期（AgentLoop 负责）：
      APPROVED → EXECUTING       (AgentLoop 在审批通过后开始执行)
      EXECUTING → COMPLETED      (执行成功)
      EXECUTING → FAILED         (执行失败 — AgentLoop 捕获异常后转换，
                                  并将错误信息回灌到 LLM 消息队列)
      DENIED → SKIPPED           (拒绝后跳过)

    等待机制说明（修复 SPEC 缺陷 2）：
      HITLManager 是同步状态机，不负责等待用户输入。
      SPEC §3.6 伪代码中的 _wait_for_resolution() 实际由 AgentLoop 实现：
      AgentLoop 调用 HITLManager.create_request() → 通过 WebSocket 推送到前端 →
      等待用户响应 → 调用 HITLManager.resolve() 或超时后 check_timeout()。
      这种分层设计使 HITLManager 可独立单测（不依赖 WebSocket/事件循环）。

    状态枚举：
      HITLState 包含全部 8 个状态（PENDING/APPROVED/DENIED/TIMEOUT/
      EXECUTING/COMPLETED/SKIPPED/FAILED），完整记录在 HITLRequest 对象上，
      形成从审批到执行的完整追溯链。
    """

    def __init__(self, timeout: int = 60):
        self._timeout = timeout
        self._requests: dict[str, HITLRequest] = {}

    def create_request(self, action: Action) -> HITLRequest:
        req = HITLRequest(
            id=str(uuid4()),
            action=action,
            state=HITLState.PENDING,
            created_at=datetime.now(),
        )
        self._requests[req.id] = req
        return req

    def resolve(self, request_id: str, decision: str) -> None:
        if request_id not in self._requests:
            raise KeyError(f"Unknown HITL request: {request_id}")
        req = self._requests[request_id]
        req.state = HITLState.APPROVED if decision == "approve" else HITLState.DENIED
        req.resolved_at = datetime.now()

    def check_timeout(self, req: HITLRequest) -> None:
        if req.state != HITLState.PENDING:
            return
        elapsed = datetime.now() - req.created_at
        if elapsed >= timedelta(seconds=self._timeout):
            req.state = HITLState.TIMEOUT
            req.resolved_at = datetime.now()

    def get_pending(self) -> list[HITLRequest]:
        return [r for r in self._requests.values() if r.state == HITLState.PENDING]
