"""Session-local track ID allocation; this does not associate detections."""

from uuid import uuid4


class SessionTrackIdFactory:
    def __init__(self) -> None:
        self._session_id = uuid4()

    def new_track_id(self) -> str:
        """Return a temporary, non-identifying ID unique within this session."""
        return f"{self._session_id}:{uuid4()}"
