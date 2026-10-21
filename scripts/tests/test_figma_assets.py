from __future__ import annotations

import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw


SPEC = importlib.util.spec_from_file_location("figma_assets", Path(__file__).resolve().parents[1] / "figma-assets.py")
assert SPEC and SPEC.loader
assets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assets)


class TransparencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "raw" / "export.png"
        self.source.parent.mkdir()
        self.reference = self.root / "source" / "asset-1-2.png"
        self.reference.parent.mkdir()
        self.output = self.root / "public" / "asset.webp"
        self.plan = self.root / "assets-plan.json"
        self.manifest = self.root / "assets-manifest.json"

    def fixture(self, *, baked: tuple[int, int, int] | None = None, opaque: bool = False) -> None:
        reference = Image.new("RGBA", (32, 32))
        source = Image.new("RGBA", reference.size)
        for y in range(32):
            for x in range(32):
                alpha = 255 if opaque else (0, 64, 128, 255)[x // 8]
                rgb = (200, 90, 40)
                reference.putpixel((x, y), (*rgb, alpha))
                actual = tuple(round(alpha / 255 * c + (1 - alpha / 255) * b) for c, b in zip(rgb, baked)) if baked else rgb
                source.putpixel((x, y), (*actual, 255 if baked else alpha))
        reference.save(self.reference)
        source.save(self.source)

    def write_plan(self, **extra: object) -> None:
        self.plan.write_text(json.dumps({"entries": [{
            "id": "1:2", "name": "asset", "kind": "image",
            "source": str(self.source), "outputPath": str(self.output),
            "referencePng": str(self.reference), "lossless": True, **extra,
        }]}), encoding="utf-8")

    def cli(self, *args: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = assets.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    @staticmethod
    def fake_tinify(source: Path, destination: Path, **_: object) -> None:
        # Exercise restoration even when compression completely destroys alpha.
        with Image.open(source) as image:
            image.convert("RGB").save(destination)

    def batch(self, *args: str) -> tuple[int, str, str]:
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("real FFmpeg/ffprobe required")
        with patch.object(assets, "tinify_compress", self.fake_tinify), patch.object(assets, "kyz_proxy_token", return_value=None):
            return self.cli("batch", str(self.plan), *args)

    def test_derives_opaque_and_native_transparent_without_declarations(self) -> None:
        for opaque in (False, True):
            with self.subTest(opaque=opaque):
                self.fixture(opaque=opaque)
                result = assets.analyze_transparency(self.source, self.reference)
                self.assertEqual(result["transparent"], not opaque)
                self.assertIsNone(result["unbake"])

    def test_infers_nondefault_baked_color(self) -> None:
        self.fixture(baked=(30, 100, 180))
        result = assets.analyze_transparency(self.source, self.reference)
        self.assertTrue(result["transparent"])
        self.assertEqual(result["unbake"], (30, 100, 180))

    def test_high_resolution_native_edges_are_not_mistaken_for_baked_black(self) -> None:
        # Native transparent RGB is undefined outside the circle; premultiplied
        # resizing must not classify those zeroes as a canvas-color composite.
        large = Image.new("RGBA", (384, 384), (0, 0, 0, 0))
        ImageDraw.Draw(large).ellipse((48, 48, 336, 336), fill=(200, 90, 40, 255))
        native = large.resize((96, 96), Image.Resampling.LANCZOS)
        native.save(self.source)
        native.resize((32, 32), Image.Resampling.LANCZOS).save(self.reference)
        result = assets.analyze_transparency(self.source, self.reference)
        self.assertIsNone(result["unbake"])
        self.write_plan()
        code, _, error = self.batch()
        self.assertEqual(code, 0, error)
        self.assertEqual(assets.read_rgba(self.output).size, (96, 96))
        self.assertTrue(assets.check_reference_alpha(self.output, self.reference))
        rendered = assets.read_rgba(self.output)
        # A low-resolution mask exposes a few pixels outside the original
        # silhouette. Those pixels must not carry black undefined source RGB.
        exposed = [
            rendered.getpixel((x, y)) for y in range(96) for x in range(96)
            if native.getpixel((x, y))[3] == 0 and rendered.getpixel((x, y))[3] >= 16
        ]
        self.assertTrue(exposed)
        self.assertTrue(all(pixel[0] > 150 for pixel in exposed))

        baked = Image.new("RGBA", native.size, (30, 100, 180, 255))
        baked.alpha_composite(native)
        baked.save(self.source)
        result = assets.analyze_transparency(self.source, self.reference)
        self.assertEqual(result["unbake"], (30, 100, 180))

    def test_missing_reference_and_legacy_override_cannot_bypass(self) -> None:
        self.fixture()
        self.write_plan()
        payload = json.loads(self.plan.read_text())
        del payload["entries"][0]["referencePng"]
        self.plan.write_text(json.dumps(payload))
        with self.assertRaisesRegex(RuntimeError, "REFERENCE_REQUIRED"):
            assets.load_plan(self.plan)
        self.write_plan(transparent=False)
        with self.assertRaisesRegex(RuntimeError, "unknown field.*transparent"):
            assets.load_plan(self.plan)
        self.write_plan(referencePng=str(self.source))
        with self.assertRaisesRegex(RuntimeError, "REFERENCE_NOT_PERSISTENT"):
            assets.load_plan(self.plan)
        self.write_plan()
        self.reference.unlink()
        code, _, error = self.batch()
        self.assertEqual(code, 1)
        self.assertIn("REFERENCE_REQUIRED", error)
        self.assertFalse(self.manifest.exists())

    def test_single_image_requires_evidence_and_repairs_automatically(self) -> None:
        self.fixture(baked=(30, 100, 180))
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as missing:
            assets.main(["image", str(self.source), str(self.output)])
        self.assertEqual(missing.exception.code, 2)
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("real FFmpeg/ffprobe required")
        with patch.object(assets, "tinify_compress", self.fake_tinify), patch.object(assets, "kyz_proxy_token", return_value=None):
            code, _, error = self.cli("image", str(self.source), str(self.output), "--reference-png", str(self.reference), "--lossless")
        self.assertEqual(code, 0, error)
        self.assertTrue(assets.check_reference_alpha(self.output, self.reference))

    def test_invalid_evidence_and_ambiguous_rgb_block_before_conversion(self) -> None:
        self.fixture()
        Image.new("RGBA", (32, 32), (0, 0, 0, 0)).save(self.reference)
        with self.assertRaisesRegex(RuntimeError, "REFERENCE_EMPTY"):
            assets.analyze_transparency(self.source, self.reference)
        Image.new("RGBA", (20, 32), (1, 2, 3, 255)).save(self.reference)
        with self.assertRaisesRegex(RuntimeError, "REFERENCE_BOUNDS_MISMATCH"):
            assets.analyze_transparency(self.source, self.reference)
        self.fixture()
        source = assets.read_rgba(self.source)
        for y in range(32):
            for x in range(24):
                source.putpixel((x, y), (0 if y < 16 else 255, 255, 255, 255))
        source.save(self.source)
        self.write_plan()
        code, _, error = self.batch()
        self.assertEqual(code, 1)
        self.assertIn("RGB_REPAIR_UNCERTAIN", error)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.manifest.exists())

    def test_real_conversion_repairs_rgb_and_preserves_all_alpha(self) -> None:
        self.fixture(baked=(30, 100, 180))
        self.write_plan()
        code, stdout, error = self.batch()
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(stdout)["total"], 1)
        with Image.open(self.output) as output:
            self.assertEqual(output.getchannel("A").tobytes(), assets.read_rgba(self.reference).getchannel("A").tobytes())
            for x in (10, 18, 26):
                actual = output.getpixel((x, 16))
                for got, expected in zip(actual[:3], (200, 90, 40)):
                    self.assertLessEqual(abs(got - expected), 3)
        manifest = json.loads(self.manifest.read_text())[0]
        self.assertEqual(manifest["alpha"]["unbakeColor"], "1e64b4")
        self.source.unlink()
        self.assertEqual(self.cli("verify", str(self.plan))[0], 0)

    def test_opaque_and_resized_outputs_restore_exact_alpha(self) -> None:
        for opaque in (False, True):
            with self.subTest(opaque=opaque):
                self.fixture(opaque=opaque)
                self.write_plan(maxWidth=16, lossless=False)
                code, _, error = self.batch("--overwrite-existing")
                self.assertEqual(code, 0, error)
                image = assets.read_rgba(self.output)
                self.assertEqual(image.size, (16, 16))
                self.assertEqual(assets.check_reference_alpha(self.output, self.reference), not opaque)
                self.assertEqual(self.cli("verify", str(self.plan))[0], 0)

    def test_incomplete_source_alpha_is_replaced(self) -> None:
        self.fixture()
        source = assets.read_rgba(self.source)
        source.putalpha(128)
        source.save(self.source)
        self.write_plan()
        code, _, error = self.batch()
        self.assertEqual(code, 0, error)
        self.assertTrue(assets.check_reference_alpha(self.output, self.reference))

    def test_repeat_requires_explicit_overwrite_and_keeps_manifest_on_failure(self) -> None:
        self.fixture()
        self.write_plan()
        self.assertEqual(self.batch()[0], 0)
        previous = self.manifest.read_bytes()
        code, _, error = self.batch()
        self.assertEqual(code, 1)
        self.assertIn("output already exists", error)
        self.assertEqual(previous, self.manifest.read_bytes())
        self.assertEqual(self.batch("--overwrite-existing")[0], 0)

    def test_verify_rejects_stale_missing_and_tampered_artifacts(self) -> None:
        self.fixture()
        self.write_plan()
        self.assertEqual(self.batch()[0], 0)
        original_manifest = self.manifest.read_bytes()
        original_reference = self.reference.read_bytes()
        original_output = self.output.read_bytes()
        self.manifest.write_text("[]")
        self.assertIn("MANIFEST_INVALID", self.cli("verify", str(self.plan))[2])
        self.manifest.write_bytes(original_manifest)
        self.write_plan(quality=60)
        self.assertIn("MANIFEST_STALE", self.cli("verify", str(self.plan))[2])
        self.write_plan()
        self.reference.write_bytes(b"changed")
        self.assertIn("REFERENCE_CHANGED", self.cli("verify", str(self.plan))[2])
        self.reference.write_bytes(original_reference)
        self.output.write_bytes(b"changed")
        self.assertIn("OUTPUT_CHANGED", self.cli("verify", str(self.plan))[2])
        self.output.write_bytes(original_output)
        image = assets.read_rgba(self.output)
        image.putalpha(128)
        image.save(self.output, lossless=True)
        manifest = json.loads(original_manifest)
        manifest[0]["sha256"] = assets.sha256(self.output)
        self.manifest.write_text(json.dumps(manifest))
        self.assertIn("ALPHA_MISMATCH", self.cli("verify", str(self.plan))[2])

    def test_empty_plan_needs_no_media_dependencies(self) -> None:
        self.plan.write_text('{"entries": []}')
        with patch.object(assets, "require_tool", side_effect=AssertionError("unexpected dependency")):
            self.assertEqual(self.cli("batch", str(self.plan))[0], 0)
            self.assertEqual(self.cli("verify", str(self.plan))[0], 0)

    def test_proxy_failure_does_not_publish_output_or_manifest(self) -> None:
        self.fixture()
        self.write_plan()
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("real FFmpeg/ffprobe required")
        with patch.object(assets, "tinify_compress", side_effect=RuntimeError("TinyPNG HTTP 429")), patch.object(assets, "kyz_proxy_token", return_value=None):
            code, _, error = self.cli("batch", str(self.plan))
        self.assertEqual(code, 1)
        self.assertIn("429", error)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.manifest.exists())
        self.assertFalse(list(self.output.parent.glob(".*.tmp*")))


if __name__ == "__main__":
    unittest.main()
