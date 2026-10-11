import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from tools.audit_apk_assets import audit, inspect_wrapper, PNG_SIG, WRAPPER_MAGIC


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

    def test_detects_nested_text1000_texture_payload(self):
        pixels = b"\x00" * 8
        texture = (
            b"text1000"
            + struct.pack("<HHHHHHI", 2, 2, 2, 2, 2, 1, 28)
            + b"\x00" * 4
            + pixels
        )
        inner_wrapper = WRAPPER_MAGIC + struct.pack("<I", len(texture)) + zlib.compress(texture)
        nested = struct.pack("<II", 2, 1) + inner_wrapper
        outer_wrapper = WRAPPER_MAGIC + struct.pack("<I", len(nested)) + zlib.compress(nested)

        result = inspect_wrapper(outer_wrapper)
        self.assertEqual(result["decoded_type"], "nested-text1000-texture-stream")
        self.assertTrue(result["nested_payload"]["inner_size_matches"])
        self.assertEqual(result["nested_payload"]["texture_width"], 2)
        self.assertEqual(result["nested_payload"]["texture_height"], 2)
        self.assertEqual(result["nested_payload"]["pixel_payload_bytes"], 8)
        self.assertTrue(result["nested_payload"]["pixel_size_matches_16bpp"])


class MapdataResourceAuditTests(unittest.TestCase):
    def test_aggregates_index_range_and_duplicate_fingerprints_without_paths(self):
        decoded = b"same opaque map data"
        wrapped = WRAPPER_MAGIC + struct.pack("<I", len(decoded)) + zlib.compress(decoded)
        png = PNG_SIG + b"\x00" * 8 + struct.pack(">II", 8, 8)
        texture = (
            b"text1000"
            + struct.pack("<HHHHHHI", 2, 2, 2, 2, 2, 1, 28)
            + b"\x00" * 4
            + b"\x00" * 8
        )
        inner_wrapper = WRAPPER_MAGIC + struct.pack("<I", len(texture)) + zlib.compress(texture)
        nested = struct.pack("<II", 2, 1) + inner_wrapper
        nested_wrapper = WRAPPER_MAGIC + struct.pack("<I", len(nested)) + zlib.compress(nested)
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "fixture.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("res/raw/mapdata000.smf", wrapped)
                archive.writestr("res/raw/mapdata001.smf", wrapped)
                archive.writestr("res/raw/mapdata003.smf", png)
                archive.writestr("res/raw/mapdata004.smf", nested_wrapper)
            report = audit(apk)

        probe = report["mapdata_resource_probe"]
        self.assertEqual(probe["resource_count"], 4)
        self.assertEqual((probe["index_min"], probe["index_max"]), (0, 4))
        self.assertEqual(probe["missing_indices_in_range"], [2])
        self.assertFalse(probe["per_file_paths_included"])
        self.assertEqual(probe["duplicate_container_groups"][0]["count"], 2)
        self.assertEqual(probe["decoded_type_counts"]["opaque-binary"], 2)
        self.assertEqual(probe["decoded_type_counts"]["png"], 1)
        self.assertEqual(probe["decoded_type_counts"]["nested-text1000-texture-stream"], 1)
        self.assertEqual(probe["nested_texture_probe"]["texture_record_count"], 1)
        self.assertEqual(probe["nested_texture_probe"]["pixel_size_matches_16bpp_count"], 1)


if __name__ == "__main__":
    unittest.main()
