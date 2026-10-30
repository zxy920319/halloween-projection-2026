import unittest

from shared.protocol import MAX_PAYLOAD_BYTES, ProtocolError, decode_packet, encode_packet


class FrameProtocolTests(unittest.TestCase):
    def test_round_trip_binary_jpeg(self):
        metadata = {
            "version": 1,
            "type": "rgb_frame",
            "frame_id": 1,
            "capture_monotonic_ns": 10,
            "width": 2,
            "height": 2,
            "encoding": "jpeg",
        }
        jpeg = b"\xff\xd8synthetic\xff\xd9"
        decoded_metadata, payload = decode_packet(encode_packet(metadata, jpeg))
        self.assertEqual(decoded_metadata, metadata)
        self.assertEqual(payload, jpeg)

    def test_rejects_bad_packets(self):
        for packet in (b"", b"\x00\x00\x00\x00", b"\x00\x00\x00\x01{"):
            with self.subTest(packet=packet), self.assertRaises(ProtocolError):
                decode_packet(packet)

    def test_rejects_bad_jpeg_and_version(self):
        metadata = {
            "version": 1,
            "type": "rgb_frame",
            "frame_id": 0,
            "capture_monotonic_ns": 1,
            "width": 1,
            "height": 1,
            "encoding": "jpeg",
        }
        with self.assertRaises(ProtocolError):
            decode_packet(encode_packet(metadata, b"not-jpeg"))
        with self.assertRaises(ProtocolError):
            decode_packet(encode_packet({"version": 2, "type": "health"}))

    def test_rejects_zero_dimensions_and_non_finite_json(self):
        metadata = {
            "version": 1,
            "type": "rgb_frame",
            "frame_id": 0,
            "capture_monotonic_ns": 1,
            "width": 0,
            "height": 1,
            "encoding": "jpeg",
        }
        with self.assertRaises(ProtocolError):
            decode_packet(encode_packet(metadata, b"\xff\xd8x\xff\xd9"))
        header = b'{"version":NaN,"type":"health"}'
        packet = len(header).to_bytes(4, "big") + header
        with self.assertRaises(ProtocolError):
            decode_packet(packet)

    def test_rejects_oversized_header(self):
        with self.assertRaises(ProtocolError):
            encode_packet({"data": "x" * 17000})

    def test_rejects_oversized_payload(self):
        with self.assertRaises(ProtocolError):
            encode_packet({"version": 1, "type": "health"}, b"x" * (MAX_PAYLOAD_BYTES + 1))
