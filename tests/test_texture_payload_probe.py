import struct
import unittest
import zlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import texture_payload_probe as probe


def texture(w=2, h=2, pixels=None):
    pixels = bytes(w * h * 2) if pixels is None else pixels
    return (probe.TEXT_MAGIC
            + struct.pack("<HHHHHHI", w, h, max(0, w - 2), max(0, h - 2), 2, 1, 28)
            + bytes(4) + pixels)


def nbc(payload, declared=None):
    declared = len(payload) if declared is None else declared
    return probe.NBC + struct.pack("<I", declared) + zlib.compress(payload)


def record(payload, declared=None):
    wrapped = nbc(payload, declared)
    return struct.pack("<II", 2, len(wrapped)) + wrapped


class TextureProbeTests(unittest.TestCase):
    def test_valid_rgba4444_header_and_pixel_length(self):
        row = probe.inspect_texture(texture())
        self.assertEqual(row["validation"], "texture_header_and_length_match")
        self.assertEqual((row["texture_width_px"], row["texture_height_px"]), (2, 2))

    def test_rejects_pixel_length_mismatch(self):
        self.assertEqual(probe.inspect_texture(texture(pixels=bytes(6)))["validation"],
                         "texture_header_length_mismatch")

    def test_parses_multiple_records(self):
        parsed = probe.parse_stream(record(texture()) + record(texture(1, 2)))
        self.assertEqual(len(parsed["records"]), 2)
        self.assertIsNone(parsed["record_error"])

    def test_preserves_png_signature_tail(self):
        parsed = probe.parse_stream(record(texture()) + probe.PNG_MAGIC + bytes(8))
        self.assertEqual(parsed["trailing_data_type"], "png_signature")

    def test_rejects_invalid_record_size(self):
        parsed = probe.parse_stream(struct.pack("<II", 2, 0xFFFFFFFF))
        self.assertEqual(parsed["record_error"], "invalid_record_size")

    def test_rejects_truncated_record_header(self):
        self.assertEqual(probe.parse_stream(b"abc")["record_error"], "truncated_record_header")

    def test_rejects_missing_inner_wrapper(self):
        raw = b"not an nbc!!"
        parsed = probe.parse_stream(struct.pack("<II", 2, len(raw)) + raw)
        self.assertEqual(parsed["record_error"], "missing_inner_nbc_header")

    def test_rejects_inner_declared_size_mismatch(self):
        parsed = probe.parse_stream(record(texture(), declared=len(texture()) + 1))
        self.assertEqual(parsed["record_error"], "nbc_declared_size_mismatch")

    def test_rejects_truncated_nbc_header(self):
        with self.assertRaisesRegex(ValueError, "truncated_nbc_header"):
            probe.decode_nbc(probe.NBC + b"x")

    def test_stops_after_valid_then_malformed_record(self):
        parsed = probe.parse_stream(record(texture()) + struct.pack("<II", 2, 0xFFFFFFFF))
        self.assertEqual(len(parsed["records"]), 1)
        self.assertEqual(parsed["record_error"], "invalid_record_size")


if __name__ == "__main__":
    unittest.main()
