import json, tempfile, unittest
from pathlib import Path
from PIL import Image
from competitor_analysis_skill.quality import assess_image
from competitor_analysis_skill.materials import standardize_material, finalize_collection, MaterialError

class QualityStage2Tests(unittest.TestCase):
    def image(self, path, fmt="PNG", size=(300,300), color=(20,40,60)):
        Image.new("RGB", size, color).save(path, format=fmt)
    def test_real_png_and_jpeg_decode(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); self.image(p/'a.png'); self.image(p/'b.jpg','JPEG')
            self.assertEqual(assess_image(p/'a.png').status,'accepted'); self.assertEqual(assess_image(p/'b.jpg').status,'accepted')
    def test_fake_truncated_small_mismatch_and_missing_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'fake.png').write_bytes(b'\x89PNG\r\n\x1a\n'+b'0'*2000); (p/'bad.jpg').write_bytes(b'not jpeg')
            self.image(p/'small.png', size=(20,20)); self.image(p/'mismatch.png','JPEG')
            self.assertEqual(assess_image(p/'fake.png').status,'rejected'); self.assertEqual(assess_image(p/'bad.jpg').status,'rejected'); self.assertEqual(assess_image(p/'small.png').status,'rejected'); self.assertEqual(assess_image(p/'mismatch.png').status,'rejected'); self.assertEqual(assess_image(p/'missing.png').status,'missing')
    def test_material_contract_and_collection_state(self):
        base={"id":"x","product_name":"P","page_name":"Page","region":"CN","product_type":"app","platform":"iOS","image_path":"assets/x.png","source_type":"user_upload","source_url":"","captured_at":"","collection_method":"user_provided","provenance":"user_upload","semantic_status":"pending","semantic_reason":"待确认","collection_status":"pending","quality_status":"accepted","quality_reason":"ok","observed_structure":[],"observed_patterns":[],"notes":""}
        self.assertEqual(finalize_collection(standardize_material(base))["collection_status"],"pending")
        base["semantic_status"]="accepted"; self.assertEqual(finalize_collection(standardize_material(base))["collection_status"],"collected")
        base["source_type"]="bad"
        with self.assertRaises(MaterialError): standardize_material(base)
    def test_duplicate_digest_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.png'; self.image(p); q=Path(d)/'b.png'; q.write_bytes(p.read_bytes())
            self.assertEqual(assess_image(p).content_sha256, assess_image(q).content_sha256)

if __name__ == '__main__': unittest.main()
