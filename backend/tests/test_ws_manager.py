import pytest


class FakeWebSocket:
    def __init__(self, fails=False):
        self.fails = fails
        self.accepted = False
        self.messages = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        if self.fails:
            raise RuntimeError("connection closed")
        self.messages.append(message)


@pytest.mark.asyncio
async def test_broadcast_delivers_to_every_connected_socket():
    from src.ws_manager import ConnectionManager

    manager = ConnectionManager()
    first, second = FakeWebSocket(), FakeWebSocket()
    await manager.connect(first)
    await manager.connect(second)

    await manager.broadcast({"type": "crossing", "direction": "IN"})

    assert first.accepted and second.accepted
    assert first.messages == [{"type": "crossing", "direction": "IN"}]
    assert second.messages == [{"type": "crossing", "direction": "IN"}]


@pytest.mark.asyncio
async def test_failed_delivery_removes_only_the_stale_socket():
    from src.ws_manager import ConnectionManager

    manager = ConnectionManager()
    healthy, stale = FakeWebSocket(), FakeWebSocket(fails=True)
    await manager.connect(healthy)
    await manager.connect(stale)

    await manager.broadcast({"type": "crossing"})
    await manager.broadcast({"type": "still-live"})

    assert healthy.messages == [{"type": "crossing"}, {"type": "still-live"}]
    assert stale not in manager.connections
