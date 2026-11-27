from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-doc-anchors.py"
SPEC = importlib.util.spec_from_file_location("check_doc_anchors", SCRIPT)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


TARGET = """\
pub fn upload_limit() -> usize {
    10 * 1024 * 1024
}

pub fn validate(size: usize) -> bool {
    size <= upload_limit()
}
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")


def verify_json(root: Path, doc: Path) -> tuple[int, dict]:
    with redirect_stdout(io.StringIO()) as captured:
        code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
    return code, json.loads(captured.getvalue())


class AnchorTests(unittest.TestCase):
    def test_print_roundtrip_and_crlf_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            noisy = TARGET.replace("    10 * 1024 * 1024", "    10 * 1024 * 1024   ").replace("\n", "\r\n")
            write(root / "src" / "upload.rs", noisy)
            with redirect_stdout(io.StringIO()) as captured:
                code = checker.main(["print", "src/upload.rs", "6", "8", "--id", "upload-validate", "--project-root", str(root)])
            self.assertEqual(code, 0)
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, f"# Upload PRD\n\n{captured.getvalue().strip()}\n")
            code, _ = verify_json(root, doc)
            self.assertEqual(code, 0)

    def test_moved_passes_while_drifted_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "src" / "upload.rs", TARGET)
            doc = root / "docs" / "prd" / "core" / "upload.md"
            line = checker.build_anchor_line(root, "src/upload.rs", 6, 8, "upload-validate")
            write(doc, f"# Upload PRD\n\n{line}\n")

            write(root / "src" / "upload.rs", "// new header\n\n" + TARGET)
            code, payload = verify_json(root, doc)
            self.assertEqual(code, 0)
            self.assertEqual((payload["moved_count"], payload["anchors"][0]["status"]), (1, "moved"))

            write(root / "src" / "upload.rs", TARGET.replace("size <= upload_limit()", "size < upload_limit()"))
            code, payload = verify_json(root, doc)
            self.assertEqual(code, 1)
            self.assertEqual(payload["findings"][0]["code"], "ANCHOR_DRIFTED")

    def test_security_and_structural_error_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "outside.rs", TARGET)
            write(root / "src" / "upload.rs", TARGET)
            valid = checker.build_anchor_line(root, "src/upload.rs", 6, 8, "dup")
            doc = root / "docs" / "prd" / "core" / "upload.md"

            cases = [
                ("<!-- t-anchor: id=escape | ../outside.rs:1-3 | sha256=" + "a" * 64 + " -->", "INVALID_TARGET_PATH"),
                ("<!-- t-anchor: id=x | src/a.rs:1-2 | sha256=deadbeef -->", "INVALID_ANCHOR_SYNTAX"),
                (f"{valid}\n\n{valid}", "DUPLICATE_ANCHOR_ID"),
            ]
            for body, expected_code in cases:
                with self.subTest(expected_code=expected_code):
                    write(doc, f"# PRD\n\n{body}\n")
                    code, payload = verify_json(root, doc)
                    self.assertEqual(code, 1)
                    self.assertEqual(payload["findings"][0]["code"], expected_code)


if __name__ == "__main__":
    unittest.main()
