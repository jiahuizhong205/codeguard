from __future__ import annotations
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from uuid import uuid4


def create_app() -> FastAPI:
    app = FastAPI(title="CodeGuard")
    sessions: dict[str, dict] = {}

    @app.post("/api/session")
    async def create_session(workspace: str = "/tmp"):
        session_id = str(uuid4())
        sessions[session_id] = {"workspace": workspace, "steps": []}
        return {"session_id": session_id}

    @app.get("/api/session/{session_id}/history")
    async def get_history(session_id: str):
        if session_id not in sessions:
            return []
        return sessions[session_id]["steps"]

    @app.post("/api/session/{session_id}/message")
    async def send_message(session_id: str, message: str = ""):
        if session_id not in sessions:
            return {"error": "Session not found"}
        return {"status": "received"}

    @app.post("/api/session/{session_id}/approve")
    async def approve_action(session_id: str, request_id: str = "", decision: str = "approve"):
        return {"status": "resolved"}

    @app.get("/api/credentials/status")
    async def credential_status():
        return {"configured": False}

    @app.get("/api/skills")
    async def list_skills():
        return {"skills": []}

    @app.get("/api/memory")
    async def get_memory():
        return {"entries": []}

    @app.websocket("/ws/session/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        await websocket.accept()
        await websocket.send_json({"type": "connected", "session_id": session_id})
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_json({"type": "echo", "data": data})
        except Exception:
            pass

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app
