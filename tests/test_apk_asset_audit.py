import struct
import unittest
import zlib
from tools.audit_apk_assets import inspect_wrapper, PNG_SIG, WRAPPER_MAGIC


class WrapperFormatTests(unittest.TestCase):
    def test_detects_direct_png(self):
        data = PNG_SIG + b"\x00" * 8 + struct.pack(">II", 16, 24) + b"\x08\x06\x00\x00\x00"
        result = inspect_wrapper(data)
        self.assertEqual(result["wrapper"], "direct-png")
        self.assertEqual(result["png_dimensions"], [16, 24])

    def test_detects_wrapper_and_validates_declared_size(self):
        decoded = b"sample opaque content"
        wrapped = WRAPPER_MAGIC + struct.pack("<I", len(decoded)) + zlib.compress(decoded)
        result = inspect_wrapper(wrapped)
        self.assertEqual(result["wrapper"], "nbc-0100-plus-zlib")
        self.assertEqual(result["decompression"], "ok")
        self.assertTrue(result["size_matches"])
        self.assertEqual(result["decoded_size"], len(decoded))

    def test_reports_size_mismatch(self):
        decoded = b"small"
        wrapped = WRAPPER_MAGIC + struct.pack("<I", len(decoded) + 2) + zlib.compress(decoded)
        result = inspect_wrapper(wrapped)
        self.assertFalse(result["size_matches"])

    def test_unknown_signature_is_not_misclassified(self):
        self.assertEqual(inspect_wrapper(b"not-a-known-format")["wrapper"], "other-signature")


if __name__ == "__main__":
    unittest.main()
