import asyncio
import logging
import queue
import threading
from dataclasses import dataclass

from websockets.asyncio.server import ServerConnection, serve

from shared.protocol import decode_packet

LOG = logging.getLogger("desktop.ingest")


@dataclass(frozen=True)
class LatestFrame:
    metadata: dict
    jpeg: bytes


class LatestFrameStore:
    """One-slot queue: replacing an unread frame always drops the older one."""

    def __init__(self) -> None:
        self.queue: queue.Queue[LatestFrame] = queue.Queue(maxsize=1)
        self.dropped_frames = 0
        self.last_frame_id: int | None = None

    def publish(self, frame: LatestFrame) -> None:
        frame_id = frame.metadata["frame_id"]
        if self.last_frame_id is not None and frame_id <= self.last_frame_id:
            self.dropped_frames += 1
            return
        self.last_frame_id = frame_id
        if self.queue.full():
            try:
                self.queue.get_nowait()
                self.dropped_frames += 1
            except queue.Empty:
                pass
        self.queue.put_nowait(frame)

    async def get(self) -> LatestFrame:
        return await asyncio.to_thread(self.queue.get)


class FrameIngestServer:
    def __init__(self, store: LatestFrameStore | None = None) -> None:
        self.store = store or LatestFrameStore()
        self.received_frames = 0

    async def handler(self, connection: ServerConnection) -> None:
        if connection.request.path != "/frames":
            await connection.close(code=1008, reason="expected /frames")
            return
        self.store.last_frame_id = None
        LOG.info("Pi transport connected from %s", connection.remote_address)
        try:
            async for message in connection:
                if not isinstance(message, bytes):
                    await connection.close(code=1003, reason="binary packets required")
                    return
                try:
                    metadata, payload = decode_packet(message)
                except ValueError as exc:
                    LOG.warning("rejecting invalid packet: %s", exc)
                    await connection.close(code=1002, reason="invalid packet")
                    return
                if metadata["type"] == "health":
                    LOG.info("source health: %s", metadata)
                    continue
                self.received_frames += 1
                self.store.publish(LatestFrame(metadata=metadata, jpeg=payload))
        except asyncio.CancelledError:
            raise
        except Exception:
            LOG.exception("frame connection failed")
        finally:
            LOG.info("Pi transport disconnected")

    async def run(
        self, host: str, port: int, ready: threading.Event | None = None
    ) -> None:
        async with serve(
            self.handler,
            host,
            port,
            max_size=6 * 1024 * 1024,
            ping_interval=20,
            ping_timeout=20,
        ):
            LOG.info("listening on ws://%s:%d/frames", host, port)
            if ready is not None:
                ready.set()
            await asyncio.Future()
