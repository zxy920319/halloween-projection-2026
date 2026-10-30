import argparse
import asyncio
import logging
import time

from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException

from pi_agent.camera.mock import MockCameraSource
from pi_agent.camera.v4l2_rgb import V4L2CameraSource
from shared.protocol import PROTOCOL_VERSION, encode_packet

LOG = logging.getLogger("pi_agent")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pi-side JPEG frame sender")
    parser.add_argument("--server", default="ws://127.0.0.1:8765/frames")
    parser.add_argument("--backend", choices=("mock", "v4l2", "orbbec_openni2"), default="mock")
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--device", default="auto", help="/dev/videoN or auto")
    parser.add_argument("--quality", type=int, default=75)
    parser.add_argument("--reconnect-max", type=float, default=10.0)
    return parser


def jpeg_bytes(rgb: bytes, width: int, height: int, quality: int) -> bytes:
    from io import BytesIO

    from PIL import Image

    output = BytesIO()
    Image.frombytes("RGB", (width, height), rgb).save(output, format="JPEG", quality=quality)
    return output.getvalue()


async def send_forever(args: argparse.Namespace) -> None:
    if args.fps <= 0 or not 1 <= args.quality <= 95 or args.reconnect_max < 1:
        raise ValueError("fps, quality, and reconnect-max must be positive valid values")
    if args.backend == "mock":
        source = MockCameraSource()
    elif args.backend == "v4l2":
        source = V4L2CameraSource(
            getattr(args, "device", "auto"),
            getattr(args, "width", 640),
            getattr(args, "height", 480),
            int(args.fps),
        )
    else:
        raise RuntimeError(f"{args.backend} backend is unsupported; use mock or v4l2")
    source.start()
    source_name = "pi5-v4l2" if args.backend == "v4l2" else "pi5-mock"
    delay = 1.0
    try:
        while True:
            try:
                async with connect(
                    args.server,
                    open_timeout=5,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=6 * 1024 * 1024,
                ) as websocket:
                    LOG.info("connected to %s", args.server)
                    delay = 1.0
                    health = {
                        "version": PROTOCOL_VERSION,
                        "type": "health",
                        "source": source_name,
                        "status": "connected",
                        "sent_monotonic_ns": time.monotonic_ns(),
                    }
                    await websocket.send(encode_packet(health))
                    frame_period = 1.0 / args.fps
                    while True:
                        started = time.monotonic()
                        frame = await asyncio.to_thread(source.read_latest)
                        if frame.jpeg is not None:
                            payload = frame.jpeg
                        else:
                            payload = await asyncio.to_thread(
                                jpeg_bytes, frame.rgb, frame.width, frame.height, args.quality
                            )
                        metadata = {
                            "version": PROTOCOL_VERSION,
                            "type": "rgb_frame",
                            "source": source_name,
                            "frame_id": frame.frame_id,
                            "capture_monotonic_ns": frame.capture_monotonic_ns,
                            "width": frame.width,
                            "height": frame.height,
                            "encoding": "jpeg",
                            "jpeg_quality": args.quality,
                            "depth_available": False,
                        }
                        await websocket.send(encode_packet(metadata, payload))
                        await asyncio.sleep(max(0.0, frame_period - (time.monotonic() - started)))
            except asyncio.CancelledError:
                raise
            except (OSError, TimeoutError, WebSocketException) as exc:
                LOG.warning("transport disconnected (%s); retrying in %.1f seconds", exc, delay)
                await asyncio.sleep(delay)
                delay = min(args.reconnect_max, delay * 2)
    finally:
        source.stop()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = make_parser().parse_args()
    try:
        asyncio.run(send_forever(args))
    except KeyboardInterrupt:
        LOG.info("stopped by user")


if __name__ == "__main__":
    main()
