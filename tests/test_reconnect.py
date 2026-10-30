import argparse
import asyncio
import unittest

from websockets.asyncio.server import serve

from pi_agent.main import send_forever


class ReconnectTests(unittest.IsolatedAsyncioTestCase):
    async def test_sender_reconnects_after_server_closes_connection(self):
        connection_count = 0
        reconnected = asyncio.Event()

        async def handler(connection):
            nonlocal connection_count
            connection_count += 1
            if connection_count >= 2:
                reconnected.set()
            await connection.close(code=1012, reason="test reconnect")

        async with serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            args = argparse.Namespace(
                fps=30,
                quality=70,
                backend="mock",
                server=f"ws://127.0.0.1:{port}/frames",
                reconnect_max=2,
            )
            task = asyncio.create_task(send_forever(args))
            try:
                await asyncio.wait_for(reconnected.wait(), timeout=4)
                self.assertGreaterEqual(connection_count, 2)
            finally:
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
