"""Versioned binary frame packet helpers shared by Pi and desktop."""

from __future__ import annotations

import json
import struct
from typing import Any

HEADER_LENGTH = struct.Struct("!I")
MAX_HEADER_BYTES = 16 * 1024
MAX_PAYLOAD_BYTES = 5 * 1024 * 1024
PROTOCOL_VERSION = 1


class ProtocolError(ValueError):
    """Raised when a packet violates framing or metadata constraints."""


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")


def encode_packet(metadata: dict[str, Any], payload: bytes = b"") -> bytes:
    if not isinstance(metadata, dict):
        raise ProtocolError("metadata must be a JSON object")
    try:
        header = json.dumps(metadata, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProtocolError(f"metadata is not valid JSON: {exc}") from exc
    if not header or len(header) > MAX_HEADER_BYTES:
        raise ProtocolError(f"header length must be between 1 and {MAX_HEADER_BYTES} bytes")
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ProtocolError(f"payload exceeds {MAX_PAYLOAD_BYTES} bytes")
    return HEADER_LENGTH.pack(len(header)) + header + payload


def decode_packet(packet: bytes) -> tuple[dict[str, Any], bytes]:
    if len(packet) < HEADER_LENGTH.size:
        raise ProtocolError("packet is shorter than the length prefix")
    (header_length,) = HEADER_LENGTH.unpack_from(packet)
    if header_length == 0 or header_length > MAX_HEADER_BYTES:
        raise ProtocolError(f"invalid header length: {header_length}")
    header_end = HEADER_LENGTH.size + header_length
    if len(packet) < header_end:
        raise ProtocolError("packet contains a truncated metadata header")
    payload = packet[header_end:]
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ProtocolError(f"payload exceeds {MAX_PAYLOAD_BYTES} bytes")
    try:
        metadata = json.loads(
            packet[HEADER_LENGTH.size:header_end].decode("utf-8"),
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ProtocolError(f"invalid metadata JSON: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ProtocolError("metadata must be a JSON object")
    if metadata.get("version") != PROTOCOL_VERSION:
        raise ProtocolError(f"unsupported protocol version: {metadata.get('version')!r}")
    message_type = metadata.get("type")
    if message_type == "rgb_frame":
        if not payload.startswith(b"\xff\xd8") or not payload.endswith(b"\xff\xd9"):
            raise ProtocolError("rgb_frame payload is not JPEG-framed")
        for field in ("frame_id", "capture_monotonic_ns", "width", "height"):
            if not isinstance(metadata.get(field), int) or metadata[field] < 0:
                raise ProtocolError(f"rgb_frame metadata has invalid {field}")
            if isinstance(metadata[field], bool):
                raise ProtocolError(f"rgb_frame metadata has invalid {field}")
        if metadata["width"] == 0 or metadata["height"] == 0:
            raise ProtocolError("rgb_frame width and height must be positive")
        if metadata.get("encoding") != "jpeg":
            raise ProtocolError("rgb_frame encoding must be jpeg")
    elif message_type == "health":
        if payload:
            raise ProtocolError("health messages must not have a payload")
    else:
        raise ProtocolError(f"unsupported message type: {message_type!r}")
    return metadata, payload
