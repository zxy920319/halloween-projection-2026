import time

from PIL import Image, ImageDraw

from pi_agent.camera.base import CameraFrame


class MockCameraSource:
    """Synthetic color bars and frame counter; it never accesses a camera."""

    def __init__(self, width: int = 640, height: int = 480) -> None:
        self.width = width
        self.height = height
        self.frame_id = 0
        self.running = False

    def start(self) -> None:
        self.running = True

    def read_latest(self) -> CameraFrame:
        if not self.running:
            raise RuntimeError("camera source is not started")
        image = Image.new("RGB", (self.width, self.height), (12, 12, 20))
        draw = ImageDraw.Draw(image)
        colors = ((220, 48, 48), (35, 170, 90), (42, 105, 220), (235, 190, 50))
        band_width = max(1, self.width // len(colors))
        for index, color in enumerate(colors):
            left = index * band_width
            draw.rectangle((left, 0, min(self.width, left + band_width), self.height), fill=color)
        draw.rectangle((0, self.height - 42, self.width, self.height), fill=(15, 15, 20))
        draw.text((12, self.height - 30), f"MOCK ONLY - frame {self.frame_id}", fill="white")
        frame = CameraFrame(
            frame_id=self.frame_id,
            capture_monotonic_ns=time.monotonic_ns(),
            width=self.width,
            height=self.height,
            rgb=image.tobytes(),
        )
        self.frame_id += 1
        return frame

    def stop(self) -> None:
        self.running = False

    def capabilities(self) -> dict[str, object]:
        return {"source": "mock", "rgb": True, "depth": False, "mock": True}
