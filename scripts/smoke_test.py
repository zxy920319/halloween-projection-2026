"""Short-lived local mock -> WebSocket ingest smoke test."""

import asyncio
import time

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from pi_agent.camera.mock import MockCameraSource
from pi_agent.main import jpeg_bytes
from shared.protocol import PROTOCOL_VERSION, decode_packet, encode_packet


async def smoke() -> None:
    packets: list[bytes] = []

    async def handler(connection):
        async for message in connection:
            packets.append(message)
            if len(packets) >= 2:
                return

    async with serve(handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        source = MockCameraSource(160, 120)
        source.start()
        async with connect(f"ws://127.0.0.1:{port}/frames") as client:
            frame = await asyncio.to_thread(source.read_latest)
            packet = encode_packet(
                {
                    "version": PROTOCOL_VERSION,
                    "type": "rgb_frame",
                    "source": "pi5-mock-smoke",
                    "frame_id": frame.frame_id,
                    "capture_monotonic_ns": frame.capture_monotonic_ns,
                    "width": frame.width,
                    "height": frame.height,
                    "encoding": "jpeg",
                },
                jpeg_bytes(frame.rgb, frame.width, frame.height, 70),
            )
            await client.send(encode_packet({"version": 1, "type": "health", "status": "ok"}))
            await client.send(packet)
            await asyncio.sleep(0.05)
        source.stop()
    frame_count = sum(decode_packet(packet)[0]["type"] == "rgb_frame" for packet in packets)
    if frame_count != 1:
        raise AssertionError(f"expected one frame packet, received {frame_count}")
    print("SMOKE_PASS: mock RGB -> JPEG binary packet -> local WebSocket server")


if __name__ == "__main__":
    asyncio.run(smoke())
