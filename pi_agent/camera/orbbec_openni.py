class OrbbecOpenNI2CameraSource:
    """Unsupported until official SDK compatibility is verified on Pi 5 ARM64."""

    def start(self) -> None:
        raise RuntimeError(
            "Astra Pro Plus/OpenNI2 capture is not implemented or verified on Pi 5 ARM64; "
            "run scripts/pi_probe.sh and consult docs/CAMERA_COMPATIBILITY.md"
        )

    def read_latest(self):
        raise RuntimeError("Orbbec/OpenNI2 camera source has not been started")

    def stop(self) -> None:
        pass

    def capabilities(self) -> dict[str, object]:
        return {
            "source": "orbbec_openni2",
            "rgb": False,
            "depth": False,
            "available": False,
        }
