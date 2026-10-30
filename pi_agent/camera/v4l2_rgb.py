"""MJPG capture through the installed v4l2-ctl tool (no extra Python dependencies)."""

import re
import subprocess
import threading
import time

from pi_agent.camera.base import CameraFrame

SOI = b"\xff\xd8"
EOI = b"\xff\xd9"
MAX_BUFFER = 8 * 1024 * 1024


def extract_jpegs(buffer: bytearray) -> list[bytes]:
    """Remove and return complete SOI..EOI frames from buffer; keep any partial tail."""
    frames: list[bytes] = []
    while True:
        start = buffer.find(SOI)
        if start < 0:
            buffer.clear()
            break
        end = buffer.find(EOI, start + 2)
        if end < 0:
            del buffer[:start]
            if len(buffer) > MAX_BUFFER:
                buffer.clear()
            break
        frames.append(bytes(buffer[start:end + 2]))
        del buffer[:end + 2]
    return frames


def parse_video_nodes(list_devices_output: str) -> list[tuple[str, list[str]]]:
    """Parse `v4l2-ctl --list-devices` into (header, [/dev/videoN...]) groups."""
    groups: list[tuple[str, list[str]]] = []
    for line in list_devices_output.splitlines():
        if not line.strip():
            continue
        if not line[0].isspace():
            groups.append((line.strip(), []))
        elif groups and re.match(r"\s*/dev/video\d+\s*$", line):
            groups[-1][1].append(line.strip())
    return groups


def find_usb_mjpg_device() -> str:
    """Pick the first MJPG-capable video node of a USB camera; raise if none."""
    listing = subprocess.run(
        ["v4l2-ctl", "--list-devices"], capture_output=True, text=True, timeout=10, check=False
    ).stdout
    for header, nodes in parse_video_nodes(listing):
        if "usb" not in header.lower():
            continue
        for node in nodes:
            formats = subprocess.run(
                ["v4l2-ctl", "-d", node, "--list-formats-ext"],
                capture_output=True, text=True, timeout=10, check=False,
            ).stdout
            if "MJPG" in formats:
                return node
    raise RuntimeError("no USB MJPG video node found; run scripts/pi_probe.sh")


class V4L2CameraSource:
    """Streams MJPG frames from v4l2-ctl and keeps only the newest one."""

    def __init__(self, device: str = "auto", width: int = 640, height: int = 480, fps: int = 30) -> None:
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._cond = threading.Condition()
        self._latest: CameraFrame | None = None
        self._last_returned = -1
        self._next_id = 0
        self._error: str | None = None
        self._stopping = False

    def start(self) -> None:
        device = find_usb_mjpg_device() if self.device == "auto" else self.device
        if not re.fullmatch(r"/dev/video\d+", device):
            raise ValueError(f"invalid video device: {device!r}")
        self.device = device
        self._stopping = False
        self._proc = subprocess.Popen(
            [
                "v4l2-ctl", "-d", device,
                f"--set-fmt-video=width={self.width},height={self.height},pixelformat=MJPG",
                f"--set-parm={self.fps}",
                "--stream-mmap=4", "--stream-to=-",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self._thread = threading.Thread(target=self._reader, name="v4l2-reader", daemon=True)
        self._thread.start()

    def _reader(self) -> None:
        proc = self._proc
        assert proc is not None and proc.stdout is not None
        buffer = bytearray()
        while True:
            chunk = proc.stdout.read(65536)
            if not chunk:
                break
            buffer.extend(chunk)
            for jpeg in extract_jpegs(buffer):
                with self._cond:
                    self._latest = CameraFrame(
                        frame_id=self._next_id,
                        capture_monotonic_ns=time.monotonic_ns(),
                        width=self.width,
                        height=self.height,
                        jpeg=jpeg,
                    )
                    self._next_id += 1
                    self._cond.notify_all()
        stderr = proc.stderr.read().decode(errors="replace").strip() if proc.stderr else ""
        with self._cond:
            if not self._stopping:
                self._error = f"v4l2-ctl exited: {stderr or 'no stderr output'}"
            self._cond.notify_all()

    def read_latest(self, timeout: float = 5.0) -> CameraFrame:
        deadline = time.monotonic() + timeout
        with self._cond:
            while True:
                if self._error:
                    raise RuntimeError(self._error)
                if self._latest is not None and self._latest.frame_id > self._last_returned:
                    self._last_returned = self._latest.frame_id
                    return self._latest
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("no fresh camera frame within timeout")
                self._cond.wait(remaining)

    def stop(self) -> None:
        with self._cond:
            self._stopping = True
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None

    def capabilities(self) -> dict[str, object]:
        return {"source": "v4l2", "rgb": True, "depth": False, "mjpg_passthrough": True}
