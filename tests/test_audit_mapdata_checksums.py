import hashlib, struct, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import audit_mapdata_checksums as audit
class MapdataChecksumTests(unittest.TestCase):
    def test_decodes_valid_nbc_wrapper(self):
        import zlib
        raw=b"small fixture"; wrapped=audit.NBC+struct.pack("<I",len(raw))+zlib.compress(raw)
        self.assertEqual(audit.decode_nbc(wrapped),raw)
    def test_rejects_nbc_declared_size_mismatch(self):
        import zlib
        with self.assertRaisesRegex(ValueError,"nbc_declared_size_mismatch"):
            audit.decode_nbc(audit.NBC+struct.pack("<I",100)+zlib.compress(b"x"))
    def test_parses_checksum_table(self):
        h1=bytes(range(32));h2=bytes(reversed(range(32)))
        rows,end=audit.parse_checksum_table(struct.pack("<I",2)+h1+h2+b"tail")
        self.assertEqual(rows,[h1,h2]);self.assertEqual(end,68)
    def test_rejects_truncated_checksum_table(self):
        with self.assertRaisesRegex(ValueError,"checksum_table_truncated"):
            audit.parse_checksum_table(struct.pack("<I",2)+bytes(32))
    def test_png_end_parses_iend(self):
        png=audit.PNG+struct.pack(">I",0)+b"IEND"+bytes(4)
        self.assertEqual(audit.png_end(png),len(png))
    def test_airport_offsets_point_to_concatenated_pngs(self):
        png=audit.PNG+struct.pack(">I",0)+b"IEND"+bytes(4);data=png+png
        info=hashlib.sha256(data).digest()+struct.pack("<I",2)+struct.pack("<II",0,len(png))
        self.assertEqual(audit.parse_airport_offsets(info,data)["count"],2)
if __name__=="__main__":unittest.main()
