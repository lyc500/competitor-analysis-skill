import json
import threading
import unittest
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from competitor_analysis_skill.browser_capture import capture_sources, _public_host
from competitor_analysis_skill.pipeline import run_pipeline


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        status = 500 if self.path == "/error" else 404 if self.path == "/missing" else 200
        if self.path == "/slow":
            import time; time.sleep(0.35)
        pages = {
            "/static": "<title>Static</title><h1 style='font-size:64px;color:#123'>Static Capture Ready</h1>",
            "/dynamic": "<title>Waiting</title><h1>Waiting</h1><script>setTimeout(()=>{document.title='Dynamic Ready';document.body.style.background='#def';document.body.innerHTML='<h1>Ready</h1>'},250)</script>",
            "/blank": "<style>html,body{margin:0;background:white}</style>",
            "/slow": "<title>Slow</title><h1>Slow</h1>",
        }
        body = pages.get(self.path, "error").encode()
        self.send_response(status); self.send_header("Content-Type", "text/html"); self.end_headers(); self.wfile.write(body)

    def log_message(self, *_args):
        pass


class CaptureWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close()

    def source(self, name, path):
        return {"id": f"src-{name}", "product_name": name, "target_page": "搜索结果页", "source_type": "public_web", "source_url": self.base + path, "normalized_url": self.base + path, "candidate_status": "pending"}

    def test_real_chromium_captures_static_and_dynamic_pages(self):
        with TemporaryDirectory() as d:
            rows = capture_sources([self.source("static", "/static"), self.source("dynamic", "/dynamic")], Path(d), settle_ms=500, allow_private_network=True)
            self.assertEqual([row["capture_status"] for row in rows], ["captured", "captured"])
            self.assertEqual(rows[1]["page_title"], "Dynamic Ready")
            for row in rows:
                path = Path(d) / row["screenshot_path"]
                with Image.open(path) as image: image.load(); self.assertEqual(image.format, "PNG")
                self.assertEqual(row["http_status"], 200); self.assertEqual(row["source_candidate_id"], "src-" + row["product_name"])
                self.assertTrue(row["browser_version"]); self.assertTrue(row["captured_at"]); self.assertEqual(row["viewport_width"], 1440)

    def test_blank_http_failure_and_batch_isolation(self):
        with TemporaryDirectory() as d:
            rows = capture_sources([self.source("one", "/static"), self.source("bad", "/missing"), self.source("blank", "/blank"), self.source("two", "/dynamic")], Path(d), settle_ms=500, allow_private_network=True)
            self.assertEqual([r["capture_status"] for r in rows], ["captured", "failed", "blank", "captured"])
            self.assertTrue(rows[1]["failure_reason"]); self.assertFalse(rows[1]["screenshot_path"])
            self.assertNotIn("semantic_status", rows[0]); self.assertNotIn("collection_status", rows[0])

    def test_http_500_is_failed_without_screenshot(self):
        with TemporaryDirectory() as d:
            row = capture_sources([self.source("server-error", "/error")], Path(d), allow_private_network=True)[0]
            self.assertEqual(row["capture_status"], "failed"); self.assertEqual(row["http_status"], 500)
            self.assertIn("HTTP 500", row["failure_reason"]); self.assertFalse(row["screenshot_path"])

    def test_browser_timeout_is_recorded_quickly(self):
        with TemporaryDirectory() as d:
            row = capture_sources([self.source("slow", "/slow")], Path(d), timeout_ms=100, settle_ms=0, allow_private_network=True)[0]
            self.assertEqual(row["capture_status"], "failed"); self.assertIn("超时", row["failure_reason"])

    def test_private_network_is_rejected_by_default(self):
        with TemporaryDirectory() as d:
            row = capture_sources([self.source("private", "/static")], Path(d))[0]
            self.assertEqual(row["capture_status"], "failed"); self.assertIn("公网", row["failure_reason"])

    def test_pipeline_persists_captures_without_material_pollution(self):
        task={"raw_request":"x","research_goal":"参考","target_page":"搜索结果页","regions":["CN"],"specified_products":["产品"],"assumptions":[],"needs_clarification":False,"task_status":"ready","planning_strategy":"user_only","competitors":[{"product_name":"产品","region":"CN","product_type":"社区","platform":"Web","target_page":"搜索结果页","planning_source":"user_specified","priority":"high","reason":"指定"}]}
        raw={"sources":[{"product_name":"产品","target_page":"搜索结果页","source_type":"public_web","source_url":"https://example.com/"}]}
        capture={"id":"cap-x","source_candidate_id":"src-x","capture_status":"failed","failure_reason":"fixture"}
        with TemporaryDirectory() as d:
            root=Path(d); source_file=root/'sources.json'; source_file.write_text(json.dumps(raw,ensure_ascii=False))
            from unittest.mock import patch
            with patch("competitor_analysis_skill.pipeline.capture_sources", return_value=[capture]):
                result=run_pipeline(task,root/'out',sources_file=source_file,capture_sources_flag=True)
            payload=json.loads(result["captures_json"].read_text())
            self.assertEqual(payload["captures"],[capture]); self.assertEqual(result["payload"]["assets"],[])

    def test_cli_requires_sources_file_for_capture_flag(self):
        completed = subprocess.run([sys.executable, "-m", "competitor_analysis_skill", "--task-file", "missing-task.json", "--capture-sources"], cwd=Path(__file__).parents[1], capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--capture-sources", completed.stderr)

    def test_formal_cli_capture_wiring_keeps_public_only_security(self):
        task={"raw_request":"x","research_goal":"参考","target_page":"搜索结果页","regions":["CN"],"specified_products":["产品"],"assumptions":[],"needs_clarification":False,"task_status":"ready","planning_strategy":"user_only","competitors":[{"product_name":"产品","region":"CN","product_type":"社区","platform":"Web","target_page":"搜索结果页","planning_source":"user_specified","priority":"high","reason":"指定"}]}
        with TemporaryDirectory() as d:
            root=Path(d); task_path=root/'task.json'; source_path=root/'sources.json'; out=root/'output'
            task_path.write_text(json.dumps(task,ensure_ascii=False)); source_path.write_text(json.dumps({"sources":[{"product_name":"产品","target_page":"搜索结果页","source_type":"public_web","source_url":self.base+"/static"}]},ensure_ascii=False))
            completed=subprocess.run([sys.executable,'-m','competitor_analysis_skill','--task-file',str(task_path),'--sources-file',str(source_path),'--capture-sources','--output',str(out)],cwd=Path(__file__).parents[1],capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            payload=json.loads((out/'captures.json').read_text()); self.assertEqual(len(payload['captures']),1); self.assertEqual(payload['captures'][0]['capture_status'],'failed'); self.assertIn('公网',payload['captures'][0]['failure_reason'])

    def test_redirect_target_private_is_rejected_by_public_only_helper(self):
        with self.assertRaises(ValueError): _public_host('http://127.0.0.1:1234/redirect')


if __name__ == "__main__": unittest.main()
