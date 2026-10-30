import asyncio
import unittest

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from desktop.ingest import FrameIngestServer
from pi_agent.camera.mock import MockCameraSource
from pi_agent.main import jpeg_bytes
from shared.protocol import encode_packet


class EndToEndMockTests(unittest.IsolatedAsyncioTestCase):
    async def test_mock_frame_reaches_latest_queue(self):
        ingest = FrameIngestServer()
        async with serve(ingest.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            source = MockCameraSource(100, 80)
            source.start()
            frame = await asyncio.to_thread(source.read_latest)
            metadata = {
                "version": 1,
                "type": "rgb_frame",
                "source": "pi5-mock-test",
                "frame_id": frame.frame_id,
                "capture_monotonic_ns": frame.capture_monotonic_ns,
                "width": frame.width,
                "height": frame.height,
                "encoding": "jpeg",
            }
            async with connect(f"ws://127.0.0.1:{port}/frames") as client:
                await client.send(encode_packet(metadata, jpeg_bytes(frame.rgb, 100, 80, 65)))
                await asyncio.sleep(0.03)
            latest = await asyncio.wait_for(ingest.store.get(), timeout=1)
            self.assertEqual(latest.metadata["source"], "pi5-mock-test")
            self.assertEqual(ingest.received_frames, 1)
            source.stop()
