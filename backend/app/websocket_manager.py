import json
from datetime import datetime, timezone
from fastapi import WebSocket
from app.logging_config import get_logger

logger = get_logger("websocket")


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "global"):
        await websocket.accept()
        if channel not in self._connections:
            self._connections[channel] = set()
        self._connections[channel].add(websocket)
        logger.info("WebSocket connected", extra={"resource_type": "websocket", "action": "connect"})

    def disconnect(self, websocket: WebSocket, channel: str = "global"):
        if channel in self._connections:
            self._connections[channel].discard(websocket)
            if not self._connections[channel]:
                del self._connections[channel]

    async def broadcast(self, event_type: str, data: dict, channel: str = "global"):
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if channel not in self._connections:
            return
        dead = []
        for ws in self._connections[channel]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[channel].discard(ws)

    async def send_personal(self, websocket: WebSocket, event_type: str, data: dict):
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        try:
            await websocket.send_text(message)
        except Exception:
            pass

    @property
    def connection_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


ws_manager = ConnectionManager()
