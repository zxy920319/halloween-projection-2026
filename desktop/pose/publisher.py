"""Broadcasts pose JSON to local consumers (Unity) on ws://host:port/poses."""

import asyncio
import json
import logging
import threading
from dataclasses import asdict

from websockets.asyncio.server import ServerConnection, serve

from shared.pose_schema import PoseFrame

LOG = logging.getLogger("desktop.pose.publisher")


def pose_to_json(pose: PoseFrame, mirrored_input: bool = False) -> str:
    return json.dumps(
        {
            "version": pose.version,
            "type": "pose",
            "frame_id": pose.frame_id,
            "server_monotonic_ns": pose.timestamp,
            "coordinate_space": "normalized_image",
            "mirrored_input": mirrored_input,
            "persons": [asdict(p) for p in pose.persons],
        },
        allow_nan=False,
    )


class PosePublisher:
    def __init__(self) -> None:
        self._clients: set[ServerConnection] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self.sent = 0

    async def _handler(self, ws: ServerConnection) -> None:
        if ws.request is None or ws.request.path != "/poses":
            await ws.close(1008, "use /poses")
            return
        self._clients.add(ws)
        try:
            await ws.wait_closed()
        finally:
            self._clients.discard(ws)

    async def _run(self, host: str, port: int, ready: threading.Event) -> None:
        self._loop = asyncio.get_running_loop()
        async with serve(self._handler, host, port):
            LOG.info("pose publisher listening on ws://%s:%d/poses", host, port)
            ready.set()
            await asyncio.Future()

    def start(self, host: str, port: int) -> None:
        ready = threading.Event()
        error: list[BaseException] = []

        def target() -> None:
            try:
                asyncio.run(self._run(host, port, ready))
            except OSError as exc:
                error.append(exc)
            finally:
                ready.set()

        threading.Thread(target=target, name="pose-publisher", daemon=True).start()
        if not ready.wait(5) or error:
            raise SystemExit(f"could not start pose publisher: {error[0] if error else 'timeout'}")

    def publish(self, message: str) -> None:
        loop = self._loop
        if loop is None or not self._clients:
            return
        for ws in list(self._clients):
            asyncio.run_coroutine_threadsafe(self._send(ws, message), loop)

    async def _send(self, ws: ServerConnection, message: str) -> None:
        try:
            await ws.send(message)
            self.sent += 1
        except Exception:
            self._clients.discard(ws)
