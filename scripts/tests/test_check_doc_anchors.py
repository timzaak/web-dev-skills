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


def anchor_for(checker_module, root: Path, target: str, start: int, end: int, anchor_id: str) -> str:
    return checker_module.build_anchor_line(root, target, start, end, anchor_id)


class AnchorVerifyTests(unittest.TestCase):
    def test_ok_anchor_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "src" / "upload.rs", TARGET)
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, f"# Upload PRD\n\n{anchor_for(checker, root, 'src/upload.rs', 6, 8, 'upload-validate')}\n")
            code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
            self.assertEqual(code, 0)

    def test_crlf_and_trailing_whitespace_are_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            noisy = TARGET.replace("    10 * 1024 * 1024", "    10 * 1024 * 1024   ")
            write(root / "src" / "upload.rs", noisy.replace("\n", "\r\n"))
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, f"# Upload PRD\n\n{anchor_for(checker, root, 'src/upload.rs', 6, 8, 'upload-validate')}\n")
            code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
            self.assertEqual(code, 0)

    def test_drifted_content_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "src" / "upload.rs", TARGET)
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, f"# Upload PRD\n\n{anchor_for(checker, root, 'src/upload.rs', 1, 3, 'upload-limit')}\n")
            write(root / "src" / "upload.rs", TARGET.replace("10 * 1024 * 1024", "20 * 1024 * 1024"))
            with redirect_stdout(io.StringIO()) as captured:
                code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
            payload = json.loads(captured.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(payload["findings"][0]["code"], "ANCHOR_DRIFTED")

    def test_moved_content_is_reported_without_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "src" / "upload.rs", TARGET)
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, f"# Upload PRD\n\n{anchor_for(checker, root, 'src/upload.rs', 6, 8, 'upload-validate')}\n")
            write(root / "src" / "upload.rs", "// new header\n\n" + TARGET)
            with redirect_stdout(io.StringIO()) as captured:
                code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
            payload = json.loads(captured.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["moved_count"], 1)
            self.assertEqual(payload["anchors"][0]["status"], "moved")

    def test_missing_target_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "src" / "upload.rs", TARGET)
            line = anchor_for(checker, root, "src/upload.rs", 6, 8, "upload-validate")
            (root / "src" / "upload.rs").unlink()
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, f"# Upload PRD\n\n{line}\n")
            with redirect_stdout(io.StringIO()) as captured:
                code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
            payload = json.loads(captured.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(payload["findings"][0]["code"], "MISSING_TARGET_FILE")

    def test_invalid_syntax_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, "# Upload PRD\n\n<!-- t-anchor: id=x | src/a.rs:1-2 | sha256=deadbeef -->\n")
            with redirect_stdout(io.StringIO()) as captured:
                code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
            payload = json.loads(captured.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(payload["findings"][0]["code"], "INVALID_ANCHOR_SYNTAX")

    def test_duplicate_id_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "src" / "upload.rs", TARGET)
            line = anchor_for(checker, root, "src/upload.rs", 6, 8, "upload-validate")
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, f"# Upload PRD\n\n{line}\n\n{line}\n")
            with redirect_stdout(io.StringIO()) as captured:
                code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
            payload = json.loads(captured.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(payload["findings"][0]["code"], "DUPLICATE_ANCHOR_ID")

    def test_target_path_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "outside.rs", TARGET)
            escape_line = "<!-- t-anchor: id=escape | ../outside.rs:1-3 | sha256=" + "a" * 64 + " -->"
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, f"# Upload PRD\n\n{escape_line}\n")
            with redirect_stdout(io.StringIO()) as captured:
                code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
            payload = json.loads(captured.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(payload["findings"][0]["code"], "INVALID_TARGET_PATH")

    def test_missing_document_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with redirect_stdout(io.StringIO()) as captured:
                code = checker.main(["verify", str(root / "docs" / "nope.md"), "--project-root", str(root), "--json"])
            payload = json.loads(captured.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(payload["findings"][0]["code"], "DOC_NOT_FOUND")


class AnchorPrintTests(unittest.TestCase):
    def test_print_output_verifies_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "src" / "upload.rs", TARGET)
            with redirect_stdout(io.StringIO()) as captured:
                code = checker.main(
                    ["print", "src/upload.rs", "6", "8", "--id", "upload-validate", "--project-root", str(root)]
                )
            self.assertEqual(code, 0)
            anchor_line = captured.getvalue().strip()
            doc = root / "docs" / "prd" / "core" / "upload.md"
            write(doc, f"# Upload PRD\n\n{anchor_line}\n")
            code = checker.main(["verify", str(doc), "--project-root", str(root), "--json"])
            self.assertEqual(code, 0)

    def test_print_rejects_out_of_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "src" / "upload.rs", TARGET)
            code = checker.main(
                ["print", "src/upload.rs", "1", "99", "--id", "bad", "--project-root", str(root)]
            )
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
