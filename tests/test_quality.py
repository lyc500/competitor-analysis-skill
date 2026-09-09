import json, tempfile, unittest
from pathlib import Path
from PIL import Image
from competitor_analysis_skill.quality import assess_image
from competitor_analysis_skill.materials import standardize_material, finalize_collection, process_materials, MaterialError

class QualityStage2Tests(unittest.TestCase):
    FIXTURES = Path(__file__).parent / 'fixtures' / 'materials'
    def image(self, path, fmt="PNG", size=(300,300), color=(20,40,60)):
        Image.new("RGB", size, color).save(path, format=fmt)
    def test_real_png_and_jpeg_decode(self):
        self.assertEqual(assess_image(self.FIXTURES/'valid.png').status,'accepted')
        self.assertEqual(assess_image(self.FIXTURES/'valid.jpg').status,'accepted')
    def test_fake_truncated_small_mismatch_and_missing_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'fake.png').write_bytes(b'\x89PNG\r\n\x1a\n'+b'0'*2000); (p/'bad.jpg').write_bytes(b'not jpeg')
            self.assertEqual(assess_image(p/'fake.png').status,'rejected'); self.assertEqual(assess_image(p/'bad.jpg').status,'rejected'); self.assertEqual(assess_image(self.FIXTURES/'small.png').status,'rejected'); self.assertEqual(assess_image(self.FIXTURES/'mismatch.png').status,'rejected'); self.assertEqual(assess_image(self.FIXTURES/'truncated.png').status,'rejected'); self.assertEqual(assess_image(self.FIXTURES/'truncated.jpg').status,'rejected'); self.assertEqual(assess_image(p/'missing.png').status,'missing')
    def test_material_contract_and_collection_state(self):
        base={"id":"x","product_name":"P","page_name":"Page","region":"CN","product_type":"app","platform":"iOS","image_path":"assets/x.png","source_type":"user_upload","source_url":"","captured_at":"","collection_method":"user_provided","provenance":"user_upload","semantic_status":"pending","semantic_reason":"待确认","collection_status":"pending","quality_status":"accepted","quality_reason":"ok","observed_structure":[],"observed_patterns":[],"notes":""}
        self.assertEqual(finalize_collection(standardize_material(base))["collection_status"],"pending")
        base["semantic_status"]="accepted"; checked=standardize_material(base); self.assertEqual(finalize_collection(checked, mechanically_verified=True)["collection_status"],"collected")
        base["source_type"]="bad"
        with self.assertRaises(MaterialError): standardize_material(base)
    def test_duplicate_digest_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.png'; self.image(p); q=Path(d)/'b.png'; q.write_bytes(p.read_bytes())
            self.assertEqual(assess_image(p).content_sha256, assess_image(q).content_sha256)

    def test_missing_file_cannot_be_collected_from_forged_quality(self):
        base=self.material('missing.png'); base.update(image_path='missing.png', quality_status='accepted', semantic_status='accepted', _mechanically_verified=True)
        result=process_materials([base], Path(tempfile.mkdtemp()))[0]
        self.assertEqual(result['quality_status'], 'missing'); self.assertNotEqual(result['collection_status'], 'collected')
        self.assertNotIn('_mechanically_verified', result)

    def material(self, image='valid.png', **overrides):
        value={"id":"m1","product_name":"P","page_name":"Page","region":"CN","product_type":"app","platform":"iOS","image_path":str(self.FIXTURES/image),"source_type":"user_upload","source_url":"","captured_at":"","collection_method":"user_provided","provenance":"user_upload","semantic_status":"pending","semantic_reason":"待确认","collection_status":"pending","quality_status":"pending","quality_reason":"","observed_structure":[],"observed_patterns":[],"notes":""}
        value.update(overrides); return value

    def test_required_text_and_duplicate_ids_are_rejected(self):
        for field in ('id','product_name','page_name'):
            with self.assertRaises(MaterialError): standardize_material(self.material(**{field:'  '}))
        with self.assertRaises(MaterialError): process_materials([self.material(), self.material(id='m1')], Path(tempfile.mkdtemp()))

    def test_duplicate_image_is_merged_without_duplicate_output_file(self):
        with tempfile.TemporaryDirectory() as d:
            result=process_materials([self.material(id='a'),self.material(id='b')],Path(d))
            self.assertEqual(result[1]['duplicate_of'],'a'); self.assertNotEqual(result[1]['collection_status'],'collected')
            self.assertFalse(result[1]['image_path'])
            self.assertTrue(all(not a.get('image_path') or (Path(d)/a['image_path']).exists() for a in result))
            self.assertEqual(len(list((Path(d)/'assets').iterdir())),1)

    def test_text_fields_are_trimmed_before_id_uniqueness(self):
        one=self.material(id=' x ', product_name=' P ', page_name=' Page ', region=' CN ', product_type=' app ', platform=' iOS ')
        normalized=standardize_material(one)
        self.assertEqual(normalized['id'],'x'); self.assertEqual(normalized['product_name'],'P'); self.assertEqual(normalized['page_name'],'Page')
        with self.assertRaises(MaterialError): process_materials([one, self.material(id='x')], Path(tempfile.mkdtemp()))

    def test_source_combinations_are_strict(self):
        valid={('user_upload','user_provided','user_upload'),('device_capture','manual_device_capture','device_capture'),('browser','browser_screenshot','online'),('public_web','web_candidate','online'),('ui_database','database_asset','online')}
        for source,method,prov in valid:
            extra = {"source_provider": "UI Database"} if source == "ui_database" else {}
            standardize_material(self.material(source_type=source,collection_method=method,provenance=prov,**extra))
        with self.assertRaises(MaterialError): standardize_material(self.material(source_type='user_upload',collection_method='web_candidate',provenance='online'))

    def test_desktop_and_mobile_web_cannot_be_collected_for_mobile_app_target(self):
        for platform in ("Web", "Mobile Web"):
            with self.subTest(platform=platform):
                material = self.material(
                    semantic_status="accepted",
                    target_surface="mobile_app",
                    target_surface_match="matched",
                    platform=platform,
                )
                result = process_materials([material], Path(tempfile.mkdtemp()))[0]
                self.assertEqual(result["quality_status"], "accepted")
                self.assertNotEqual(result["collection_status"], "collected")

    def test_ui_database_material_preserves_mobile_target_and_source_metadata(self):
        material = self.material(
            semantic_status="accepted",
            target_surface="mobile_app",
            target_surface_match="matched",
            platform="iOS",
            source_type="ui_database",
            source_provider="Refero",
            source_url="https://refero.design/apps/example",
            source_asset_url="https://cdn.example.com/screen.png",
            collection_method="database_asset",
            provenance="online",
        )
        result = process_materials([material], Path(tempfile.mkdtemp()))[0]
        self.assertEqual(result["collection_status"], "collected")
        self.assertEqual(result["target_surface"], "mobile_app")
        self.assertEqual(result["source_provider"], "Refero")
        invalid = dict(material, source_provider="")
        with self.assertRaisesRegex(MaterialError, "source_provider"):
            standardize_material(invalid)

if __name__ == '__main__': unittest.main()
