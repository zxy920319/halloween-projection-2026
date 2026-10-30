class V4L2CameraSource:
    """Explicit placeholder until a tested V4L2 device-selection adapter exists."""

    def start(self) -> None:
        raise RuntimeError(
            "V4L2 capture is not implemented; run scripts/pi_probe.sh and "
            "do not treat this backend as camera support"
        )

    def read_latest(self):
        raise RuntimeError("V4L2 camera source has not been started")

    def stop(self) -> None:
        pass

    def capabilities(self) -> dict[str, object]:
        return {"source": "v4l2", "rgb": False, "depth": False, "available": False}
