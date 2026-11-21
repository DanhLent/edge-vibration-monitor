import hashlib
from pathlib import Path
import re
import unittest

from scripts.extract_requirements import extract

ROOT = Path(__file__).resolve().parents[1]


class RequirementTests(unittest.TestCase):
    def test_documentation_scope_and_routing(self):
        text = (ROOT / "docs/requirements.md").read_text()
        self.assertLess(len((ROOT / "AGENTS.md").read_text().splitlines()), 60)
        for path in re.findall(r"docs/[A-Za-z0-9_/-]+\.md", (ROOT / "AGENTS.md").read_text()):
            self.assertTrue((ROOT / path).is_file(), path)
        for name in ("Lê Nguyễn Thành Danh", "Trần Minh Nhật", "Nguyễn Tiến Đạt"):
            self.assertIn(name, text)
        self.assertIn("100%", text)
        self.assertIn("30%", text)

    def test_optional_local_workbook_preservation(self):
        source = ROOT / "DeTai_BTL_CE339_2026.xlsx"
        if not source.is_file():
            self.skipTest("Original workbook is local-only; public clones verify scoped documentation")
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        text = extract(source)
        for name in ("Lê Nguyễn Thành Danh", "Trần Minh Nhật", "Nguyễn Tiến Đạt"):
            self.assertIn(name, text)
        for code in ("N07", "E1", "E3", "E4", "E5"):
            self.assertIsNone(re.search(r"(?<![A-Za-z0-9])" + code + r"(?![A-Za-z0-9])", text), code)
        self.assertIn("100%", text)
        self.assertIn("30%", text)
        self.assertEqual(before, hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(text, (ROOT / "docs/requirements.md").read_text())
