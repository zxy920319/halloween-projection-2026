import unittest

from pi_agent.camera.v4l2_rgb import extract_jpegs, parse_video_nodes

LISTING = """pispbe (platform:1000880000.pisp_be):
        /dev/video20
        /dev/media0

USB 2.0 Camera: USB Camera (usb-xhci-hcd.0-1.2):
        /dev/video0
        /dev/video1
        /dev/media3
"""


class V4L2HelperTests(unittest.TestCase):
    def test_extract_jpegs_handles_split_and_partial_frames(self):
        a = b"\xff\xd8aaa\xff\xd9"
        b = b"\xff\xd8bbb\xff\xd9"
        buffer = bytearray(b"junk" + a + b[:4])
        self.assertEqual(extract_jpegs(buffer), [a])
        buffer.extend(b[4:])
        self.assertEqual(extract_jpegs(buffer), [b])
        self.assertEqual(len(buffer), 0)

    def test_parse_video_nodes_ignores_media_nodes(self):
        groups = dict(parse_video_nodes(LISTING))
        self.assertEqual(groups["USB 2.0 Camera: USB Camera (usb-xhci-hcd.0-1.2):"], ["/dev/video0", "/dev/video1"])
