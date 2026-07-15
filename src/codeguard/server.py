from __future__ import annotations
from fastapi import FastAPI, WebSocket, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from uuid import uuid4
import json
import asyncio

from codeguard.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, is_configured
from codeguard.models.entities import LLMResponse


def create_app() -> FastAPI:
    app = FastAPI(title="CodeGuard")
    sessions: dict[str, dict] = {}

    @app.post("/api/session")
    async def create_session(workspace: str = "/tmp"):
        session_id = str(uuid4())
        sessions[session_id] = {"workspace": workspace, "steps": [], "artifacts": {}}
        return {"session_id": session_id}

    @app.get("/api/session/{session_id}/history")
    async def get_history(session_id: str):
        if session_id not in sessions:
            return []
        return sessions[session_id]["steps"]

    @app.get("/api/session/{session_id}/artifacts")
    async def list_artifacts(session_id: str):
        if session_id not in sessions:
            return {"artifacts": []}
        arts = sessions[session_id].get("artifacts", {})
        return {"artifacts": [{"filename": k, "size": len(v)} for k, v in arts.items()]}

    @app.get("/api/session/{session_id}/artifacts/{filename:path}")
    async def download_artifact(session_id: str, filename: str):
        if session_id not in sessions:
            return {"error": "Session not found"}
        arts = sessions[session_id].get("artifacts", {})
        if filename not in arts:
            return {"error": "File not found"}
        content = arts[filename]
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{Path(filename).name}"'}
        )

    @app.post("/api/session/{session_id}/message")
    async def send_message(session_id: str, body: dict = None):
        if session_id not in sessions:
            return {"error": "Session not found"}

        message = (body or {}).get("message", "")
        ws = sessions[session_id].get("websocket")

        if not is_configured():
            return {"error": "LLM not configured. Edit .env file first."}

        task = asyncio.create_task(_run_agent(session_id, message, sessions, ws))
        return {"status": "started"}

    @app.post("/api/session/{session_id}/approve")
    async def approve_action(session_id: str, body: dict = None):
        request_id = (body or {}).get("request_id", "")
        decision = (body or {}).get("decision", "approve")
        return {"status": "resolved"}

    @app.get("/api/credentials/status")
    async def credential_status():
        return {"configured": is_configured(), "base_url": LLM_BASE_URL, "model": LLM_MODEL}

    @app.get("/api/skills")
    async def list_skills():
        return {"skills": []}

    @app.get("/api/memory")
    async def get_memory():
        return {"entries": []}

    @app.websocket("/ws/session/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in sessions:
            sessions[session_id] = {"workspace": "/tmp", "steps": []}
        sessions[session_id]["websocket"] = websocket
        await websocket.send_json({"type": "connected", "session_id": session_id})
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("type") == "message":
                    await _run_agent(session_id, msg.get("content", ""), sessions, websocket)
        except Exception:
            pass
        finally:
            if session_id in sessions:
                sessions[session_id].pop("websocket", None)

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


async def _run_agent(session_id: str, task: str, sessions: dict, ws: WebSocket | None):
    from codeguard.agent.llm_client import RealLLMClient
    from codeguard.agent.loop import AgentLoop
    from codeguard.tools.dispatcher import ToolDispatcher
    from codeguard.tools.file_tools import ReadFile, WriteFile, EditFile, ListFiles, SearchContent
    from codeguard.tools.shell_tools import RunShell
    from codeguard.tools.test_tools import RunTests, RunLint
    from codeguard.governance.guardrail import GuardrailEngine
    from codeguard.governance.rules import default_rules
    from codeguard.governance.hitl import HITLManager
    from codeguard.governance.audit_log import AuditLog
    from codeguard.governance.scope_fence import ScopeFence
    from codeguard.feedback.validators import TestValidator
    from codeguard.memory.store import MemoryStore
    from codeguard.skills.loader import SkillLoader

    workspace = Path(sessions[session_id].get("workspace", "/tmp"))
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / ".codeguard").mkdir(exist_ok=True)

    dispatcher = ToolDispatcher()
    dispatcher.register(ReadFile(workspace))
    dispatcher.register(WriteFile(workspace))
    dispatcher.register(EditFile(workspace))
    dispatcher.register(ListFiles(workspace))
    dispatcher.register(SearchContent(workspace))
    dispatcher.register(RunShell())
    dispatcher.register(RunTests())
    dispatcher.register(RunLint())

    loop = AgentLoop(
        llm_client=RealLLMClient(LLM_BASE_URL, LLM_API_KEY, LLM_MODEL),
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

    async def send_step(step):
        if ws:
            step_data = {
                "step_index": step.step_index,
                "step_type": step.step_type.value,
                "content": step.content if isinstance(step.content, str) else str(step.content),
            }
            if step.step_type.value == "file_output" and isinstance(step.content, dict):
                fname = step.content.get("filename", "unknown")
                fcontent = step.content.get("content", "")
                sessions[session_id].setdefault("artifacts", {})[fname] = fcontent
                step_data["content"] = step.content
            await ws.send_json({"type": "step", "step": step_data})

    try:
        if ws:
            await ws.send_json({"type": "status", "message": "正在初始化 Agent..."})

        steps = await loop.run(task, on_step=send_step)

        for step in steps:
            step_record = {
                "step_index": step.step_index,
                "step_type": step.step_type.value,
                "content": step.content if isinstance(step.content, str) else str(step.content),
            }
            if step.step_type.value == "file_output" and isinstance(step.content, dict):
                fname = step.content.get("filename", "unknown")
                fcontent = step.content.get("content", "")
                sessions[session_id].setdefault("artifacts", {})[fname] = fcontent
                step_record["content"] = step.content
            sessions[session_id]["steps"].append(step_record)

        if ws:
            await ws.send_json({"type": "done"})
    except Exception as e:
        err_msg = f"Agent error: {type(e).__name__}: {e}"
        if ws:
            await ws.send_json({"type": "error", "message": err_msg})
        else:
            raise
