import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from competitor_analysis_skill.source_discovery import SourceDiscoveryError, process_sources, normalize_url
from competitor_analysis_skill.pipeline import run_pipeline


class SourceDiscoveryTests(unittest.TestCase):
    def task(self):
        return {"raw_request":"x","research_goal":"页面参考","target_page":"搜索结果页","regions":["CN"],"specified_products":["小红书"],"assumptions":[],"needs_clarification":False,"task_status":"ready","planning_strategy":"user_only","competitors":[{"product_name":"小红书","region":"CN","product_type":"社区","platform":"Web","target_page":"搜索结果页","planning_source":"user_specified","priority":"high","reason":"指定"}]}
    def candidate(self, **overrides):
        value={"product_name":"小红书","target_page":"搜索结果页","source_type":"public_web","source_url":"HTTPS://Example.COM:443/page#section"}
        value.update(overrides); return value

    def test_normalizes_url_and_persists_pending_candidate(self):
        result=process_sources(self.task(), [self.candidate()])
        self.assertEqual(result[0]["normalized_url"],"https://example.com/page")
        self.assertEqual(result[0]["candidate_status"],"pending")
        self.assertTrue(result[0]["id"])

    def test_rejects_invalid_urls_and_source_type(self):
        for url in ("javascript:alert(1)","data:text/plain,x","file:///tmp/a","/relative","https:///missing"):
            with self.assertRaises(SourceDiscoveryError): process_sources(self.task(), [self.candidate(source_url=url)])
        with self.assertRaises(SourceDiscoveryError): process_sources(self.task(), [self.candidate(source_type="browser")])

    def test_rejects_unplanned_product_and_wrong_page(self):
        with self.assertRaises(SourceDiscoveryError): process_sources(self.task(), [self.candidate(product_name="其他")])
        with self.assertRaises(SourceDiscoveryError): process_sources(self.task(), [self.candidate(target_page="个人主页")])

    def test_dedupes_per_product_but_keeps_cross_product_relationship(self):
        task=self.task(); task["specified_products"]=["小红书","抖音"]; task["competitors"].append({**task["competitors"][0],"product_name":"抖音"})
        rows=process_sources(task,[self.candidate(),self.candidate(source_url="https://example.com/page"),self.candidate(product_name="抖音")])
        self.assertEqual(len(rows),2); self.assertEqual(rows[0]["product_name"],"小红书"); self.assertEqual(rows[1]["product_name"],"抖音")

    def test_rejects_material_fields_and_forced_states(self):
        with self.assertRaises(SourceDiscoveryError): process_sources(self.task(), [self.candidate(collection_status="collected")])
        with self.assertRaises(SourceDiscoveryError): process_sources(self.task(), [self.candidate(image_path="x.png")])

    def test_pipeline_sources_file_does_not_call_network_or_collector(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); task_path=root/'task.json'; source_path=root/'sources.json'; out=root/'out'
            task_path.write_text(json.dumps(self.task(),ensure_ascii=False)); source_path.write_text(json.dumps({"sources":[self.candidate()]},ensure_ascii=False))
            with patch("competitor_analysis_skill.collector.urlopen", side_effect=AssertionError("network called")):
                result=run_pipeline(json.loads(task_path.read_text()),out,materials_file=None,sources_file=source_path)
            payload=json.loads((out/'sources.json').read_text()); self.assertEqual(len(payload["sources"]),1); self.assertEqual(payload["sources"][0]["candidate_status"],"pending")
            self.assertFalse(payload["sources"][0].get("image_path")); self.assertTrue(result["sources_json"].exists())

    def test_sources_file_requires_structured_task(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'sources.json'; path.write_text(json.dumps({"sources":[self.candidate()]}))
            with self.assertRaises(Exception): run_pipeline("legacy request",Path(d)/'out',sources_file=path)

if __name__ == '__main__': unittest.main()
