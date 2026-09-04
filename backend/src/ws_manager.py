"""WebSocket connection fan-out."""

import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    @property
    def active_connections(self) -> set[WebSocket]:
        return self.connections

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        if hasattr(message, "model_dump"):
            message = message.model_dump(mode="json")
        connections = list(self.connections)
        if not connections:
            return
        results = await asyncio.gather(
            *(websocket.send_json(message) for websocket in connections), return_exceptions=True
        )
        for websocket, result in zip(connections, results):
            if isinstance(result, Exception):
                self.disconnect(websocket)
