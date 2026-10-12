import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import audit_efile_dex_mapping as mapping

class DexResourceMappingTests(unittest.TestCase):
    def test_reads_uleb128_single_byte(self):
        self.assertEqual(mapping.uleb(b"\x7f", 0), (127, 1))
    def test_reads_uleb128_multibyte(self):
        self.assertEqual(mapping.uleb(b"\xac\x02", 0), (300, 2))
    def test_rejects_truncated_uleb128(self):
        with self.assertRaisesRegex(ValueError, "truncated_uleb128"):
            mapping.uleb(b"\x80", 0)
    def test_rejects_non_dex_input(self):
        with self.assertRaisesRegex(ValueError, "not_standard_dex"):
            mapping.DexFile(b"not a dex")
    def test_instruction_payload_size_for_array_data(self):
        payload = struct.pack("<HHI", 0x0300, 4, 3) + bytes(12)
        self.assertEqual(mapping.skip_payload(payload, 0), 10)
    def test_known_native_table_constants(self):
        self.assertEqual(mapping.DEFAULT_EFILE_COUNT, 442)
        self.assertEqual(mapping.DEFAULT_TABLE_VADDR, 0x002E1108)

if __name__ == "__main__":
    unittest.main()
