import asyncio
import json
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel

from memory import Memory
from brain import Brain
from tools import TOOL_MAP
from logger import log

app = FastAPI(title="ATIG v2.0", docs_url=None, redoc_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1000)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
memory = Memory()
brain = Brain(memory)
active_connections = []

PAGES = {
    "/": "chat.html",
    "/sphere": "index.html",
}

def make_handler(path):
    async def handler():
        return FileResponse(path)
    return handler


for route, html in PAGES.items():
    path = os.path.join(BASE_DIR, html)
    app.add_api_route(route, make_handler(path), methods=["GET"])


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    session_id = str(id(websocket))

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            user_message = payload.get("message", "").strip()

            if not user_message:
                continue

            if len(user_message) > 20000:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "Сообщение слишком длинное."
                }))
                continue

            await memory.store_message(
                "user",
                user_message,
                session_id=session_id
            )

            await websocket.send_text(json.dumps({
                "type": "thinking",
                "content": "..."
            }))

            try:
                response_text, actions = await brain.think(
                    user_message,
                    session_id=session_id
                )
            except Exception as e:
                log.error(f"Brain error: {e}")
                response_text = "Произошла ошибка. Попробуйте снова."
                actions = []

            await memory.store_message(
                "assistant",
                response_text,
                session_id=session_id
            )

            await websocket.send_text(json.dumps({
                "type": "message",
                "role": "assistant",
                "content": response_text,
                "actions": actions,
                "timestamp": datetime.utcnow().isoformat()
            }))

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

    except Exception as e:
        log.error(f"WebSocket error: {e}")

        if websocket in active_connections:
            active_connections.remove(websocket)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


@app.post("/api/chat")
async def chat_api(req: ChatRequest):

    if not req.message.strip():
        raise HTTPException(400, "Пустое сообщение")

    await memory.store_message(
        "user",
        req.message,
        session_id=req.session_id
    )

    response_text, actions = await brain.think(
        req.message,
        session_id=req.session_id
    )

    await memory.store_message(
        "assistant",
        response_text,
        session_id=req.session_id
    )

    return JSONResponse({
        "reply": response_text,
        "actions": actions
    })


@app.delete("/api/history")
async def clear_history(session_id: str = "default"):
    await memory.clear_session(session_id)

    return JSONResponse({
        "status": "История очищена"
    })


@app.get("/api/status")
async def status():
    count = await memory.get_message_count()

    return JSONResponse({
        "status": "online",
        "version": "2.0",
        "messages": count,
        "tools": len(TOOL_MAP)
    })


@app.get("/{path:path}")
async def static_files(path: str):

    file_path = os.path.join(BASE_DIR, path)

    if os.path.isfile(file_path):
        return FileResponse(file_path)

    raise HTTPException(404, "Не найдено")


@app.on_event("startup")
async def startup():
    log.info("🧠 ATIG v2.0 запускается...")
    await memory.set_state("status", "running")


@app.on_event("shutdown")
async def shutdown():
    await memory.set_state("status", "stopped")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )