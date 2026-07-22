import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

import build_global_tool


ROOT = Path(__file__).resolve().parents[1]


class AtlasHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.inline_styles = []
        self.csp = ""

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.append(values["id"])
        if "style" in values:
            self.inline_styles.append((tag, values["style"]))
        if tag == "meta" and values.get("http-equiv", "").lower() == "content-security-policy":
            self.csp = values.get("content", "")


class GeneratedToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        cls.script = re.search(r"<script>(.*)</script>", cls.html, re.S).group(1)
        cls.styles = re.search(r"<style>(.*)</style>", cls.html, re.S).group(1)
        cls.parser = AtlasHTMLParser()
        cls.parser.feed(cls.html)

    def test_inline_assets_match_hashed_content_security_policy(self):
        self.assertIn(
            f"script-src 'sha256-{build_global_tool.csp_hash(self.script)}'",
            self.parser.csp,
        )
        self.assertIn(
            f"style-src 'sha256-{build_global_tool.csp_hash(self.styles)}'",
            self.parser.csp,
        )
        self.assertNotIn("'unsafe-inline'", self.parser.csp)
        self.assertEqual(self.parser.inline_styles, [])

    def test_document_ids_are_unique(self):
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))

    def test_javascript_syntax(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        result = subprocess.run(
            [node, "--check"],
            input=self.script,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_external_runtime_dependencies(self):
        self.assertNotRegex(self.html, r"<(?:script|link)[^>]+(?:src|href)=[\"']https?://")
        self.assertNotRegex(self.script, r"fetch\([\"']https?://")


if __name__ == "__main__":
    unittest.main()
