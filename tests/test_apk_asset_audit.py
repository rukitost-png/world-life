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

    def test_reports_truncated_type2_record_header(self):
        wrapped = WRAPPER_MAGIC + struct.pack("<I", 4) + zlib.compress(struct.pack("<I", 2))
        result = inspect_wrapper(wrapped)
        self.assertEqual(result["decoded_type"], "nested-nbc-unverified")
        self.assertEqual(result["nested_payload"]["record_error"], "truncated-record-header")

    def test_reports_malformed_first_type2_record_size(self):
        malformed = struct.pack("<II", 2, 0) + bytes(12)
        wrapped = WRAPPER_MAGIC + struct.pack("<I", len(malformed)) + zlib.compress(malformed)
        result = inspect_wrapper(wrapped)
        self.assertEqual(result["decoded_type"], "nested-nbc-unverified")
        self.assertEqual(result["nested_payload"]["record_error"], "invalid-record-size")
        self.assertEqual(result["nested_payload"]["record_count"], 0)

    def test_reports_missing_inner_wrapper_on_first_type2_record(self):
        malformed = struct.pack("<II", 2, 12) + bytes(12)
        wrapped = WRAPPER_MAGIC + struct.pack("<I", len(malformed)) + zlib.compress(malformed)
        result = inspect_wrapper(wrapped)
        self.assertEqual(result["decoded_type"], "nested-nbc-unverified")
        self.assertEqual(result["nested_payload"]["record_error"], "missing-inner-nbc-header")

    def test_does_not_certify_stream_with_later_malformed_record(self):
        texture = (
            b"text1000"
            + struct.pack("<HHHHHH", 2, 2, 2, 2, 2, 1) + struct.pack("<I", 28)
            + bytes(4)
            + bytes(8)
        )
        inner_wrapper = WRAPPER_MAGIC + struct.pack("<I", len(texture)) + zlib.compress(texture)
        valid_record = struct.pack("<II", 2, len(inner_wrapper)) + inner_wrapper
        malformed_record = struct.pack("<II", 2, 0) + bytes(12)
        nested = valid_record + malformed_record
        wrapped = WRAPPER_MAGIC + struct.pack("<I", len(nested)) + zlib.compress(nested)

        result = inspect_wrapper(wrapped)
        self.assertEqual(result["decoded_type"], "nested-nbc-unverified")
        self.assertEqual(result["nested_payload"]["texture_count"], 1)
        self.assertEqual(result["nested_payload"]["record_error"], "invalid-record-size")

    def test_detects_nested_text1000_texture_payload(self):
        pixels = b"\x00" * 8
        texture = (
            b"text1000"
            + struct.pack("<HHHHHH", 2, 2, 2, 2, 2, 1) + struct.pack("<I", 28)
            + b"\x00" * 4
            + pixels
        )
        inner_wrapper = WRAPPER_MAGIC + struct.pack("<I", len(texture)) + zlib.compress(texture)
        nested = struct.pack("<II", 2, len(inner_wrapper)) + inner_wrapper
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
            + struct.pack("<HHHHHH", 2, 2, 2, 2, 2, 1) + struct.pack("<I", 28)
            + b"\x00" * 4
            + b"\x00" * 8
        )
        inner_wrapper = WRAPPER_MAGIC + struct.pack("<I", len(texture)) + zlib.compress(texture)
        record_one = struct.pack("<II", 2, len(inner_wrapper)) + inner_wrapper
        texture_two = (
            b"text1000"
            + struct.pack("<HHHHHH", 1, 1, 1, 1, 2, 1) + struct.pack("<I", 28)
            + b"\x00" * 4
            + b"\x00" * 2
        )
        inner_wrapper_two = WRAPPER_MAGIC + struct.pack("<I", len(texture_two)) + zlib.compress(texture_two)
        record_two = struct.pack("<II", 2, len(inner_wrapper_two)) + inner_wrapper_two
        nested = record_one + record_two + png + b"tail"
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
        self.assertEqual(probe["nested_texture_probe"]["texture_record_count"], 2)
        self.assertEqual(probe["nested_texture_probe"]["pixel_size_matches_16bpp_count"], 2)
        self.assertEqual(probe["nested_texture_probe"]["trailing_png_stream_count"], 1)


if __name__ == "__main__":
    unittest.main()
