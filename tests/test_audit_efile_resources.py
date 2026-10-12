import struct, tempfile, unittest, zipfile, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import audit_efile_resources as audit

def synthetic_elf():
    blob = bytearray(0x300)
    blob[:16] = b"\x7fELF" + bytes([1, 1, 1]) + bytes(9)
    struct.pack_into("<I", blob, 28, 52)
    struct.pack_into("<H", blob, 42, 32)
    struct.pack_into("<H", blob, 44, 1)
    struct.pack_into("<IIIIIIII", blob, 52, 1, 0, 0, 0, len(blob), len(blob), 5, 0x1000)
    struct.pack_into("<II", blob, 0x100, 0x180, 0x194)
    blob[0x180:0x18e] = b"maptexinfo.dat\0"
    blob[0x194:0x1a3] = b"mapdata000.nbc\0"
    return bytes(blob)

class EfileAuditTests(unittest.TestCase):
    def test_extracts_pointer_table_strings(self):
        rows = audit.extract_filename_table(synthetic_elf(), 0x100, 2)
        self.assertEqual([r["logical_filename"] for r in rows], ["maptexinfo.dat", "mapdata000.nbc"])
    def test_generates_smf_candidates(self):
        self.assertEqual(audit.candidate_archive_names("maptexinfo.dat"), ["maptexinfo.dat", "maptexinfo.smf"])
        self.assertEqual(audit.candidate_archive_names("mapdata000.nbc"), ["mapdata000.nbc", "mapdata000.smf"])
    def test_basename_match_is_not_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            apk = Path(tmp) / "tiny.apk"
            with zipfile.ZipFile(apk, "w") as zf:
                zf.writestr("res/raw/maptexinfo.smf", b"fixture")
                zf.writestr("res/raw/mapdata000.smf", b"fixture2")
            report = audit.audit(synthetic_elf(), apk, 0x100, 2)
        self.assertEqual(report["entries"][0]["candidate_archive_entries"], ["res/raw/maptexinfo.smf"])
        self.assertFalse(report["entries"][0]["mapping_proven"])
    def test_rejects_non_elf(self):
        with self.assertRaisesRegex(ValueError, "not_elf"):
            audit.extract_filename_table(b"not an elf", 0x100, 1)
    def test_rejects_bad_table_address(self):
        with self.assertRaisesRegex(ValueError, "vaddr_not_in_file_backed_load_segment"):
            audit.extract_filename_table(synthetic_elf(), 0x500, 1)
    def test_rejects_truncated_table(self):
        with self.assertRaisesRegex(ValueError, "filename_pointer_table_truncated"):
            audit.extract_filename_table(synthetic_elf(), 0x2fc, 2)

if __name__ == "__main__":
    unittest.main()
