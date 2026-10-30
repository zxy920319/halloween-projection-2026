from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CameraFrame:
    frame_id: int
    capture_monotonic_ns: int
    width: int
    height: int
    rgb: bytes | None = None
    jpeg: bytes | None = None


class CameraSource(Protocol):
    def start(self) -> None: ...

    def read_latest(self) -> CameraFrame: ...

    def stop(self) -> None: ...

    def capabilities(self) -> dict[str, object]: ...
