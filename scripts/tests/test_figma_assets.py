from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
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

    def test_native_nearly_invisible_rgb_is_compared_as_visible_contribution(self) -> None:
        self.fixture()
        reference = assets.read_rgba(self.reference)
        source = assets.read_rgba(self.source)
        for y in range(32):
            for x in range(8):
                reference.putpixel((x, y), (255, 255, 255, 1))
                source.putpixel((x, y), (0, 0, 0, 1))
        reference.save(self.reference)
        source.save(self.source)
        # RGB differs by 255, but rendered contribution differs by only 1.
        self.assertIsNone(assets.analyze_transparency(self.source, self.reference)["unbake"])

    def test_different_native_rasterization_rates_have_a_common_sampling_grid(self) -> None:
        source = Image.new("RGBA", (384, 256), (0, 0, 0, 0))
        draw = ImageDraw.Draw(source)
        draw.ellipse((19, 7, 367, 249), fill=(245, 240, 235, 255))
        draw.polygon([(40, 20), (355, 70), (125, 244)], fill=(30, 60, 90, 255))
        source.save(self.source)
        source.resize((48, 32), Image.Resampling.BILINEAR).save(self.reference)
        result = assets.analyze_transparency(self.source, self.reference)
        self.assertTrue(result["transparent"])
        self.assertIsNone(result["unbake"])

    def test_native_alpha_does_not_hide_opaque_or_visible_edge_mismatch(self) -> None:
        self.fixture()
        source = assets.read_rgba(self.source)
        for y in range(32):
            for x in range(24, 32):
                source.putpixel((x, y), (5, 240, 210, 255))
        source.save(self.source)
        with self.assertRaisesRegex(RuntimeError, "REFERENCE_RGB_MISMATCH"):
            assets.analyze_transparency(self.source, self.reference)
        self.fixture()
        source = assets.read_rgba(self.source)
        for y in range(32):
            for x in range(8, 24):
                source.putpixel((x, y), (0 if y < 16 else 255, 255, 255, source.getpixel((x, y))[3]))
        source.save(self.source)
        with self.assertRaisesRegex(RuntimeError, "RGB_REPAIR_UNCERTAIN"):
            assets.analyze_transparency(self.source, self.reference)

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

    def test_verify_rejects_png_disguised_as_webp(self) -> None:
        self.fixture()
        self.write_plan()
        self.assertEqual(self.batch()[0], 0)
        assets.read_rgba(self.output).save(self.output, format="PNG")
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest[0]["sha256"] = assets.sha256(self.output)
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertIn("TYPE_MISMATCH", self.cli("verify", str(self.plan))[2])

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


class SvgTypeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.svg"
        self.source.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 12">'
            '<path d="M0 0h24v12H0z"/></svg>',
            encoding="utf-8-sig",
        )
        self.output = self.root / "logo.svg"
        self.plan = self.root / "assets-plan.json"
        self.manifest = self.root / "assets-manifest.json"
        self.write_plan()

    def write_plan(self, **extra: object) -> None:
        self.plan.write_text(json.dumps({"entries": [{
            "id": "1:5", "name": "logo", "kind": "svg",
            "source": str(self.source), "outputPath": str(self.output), **extra,
        }]}), encoding="utf-8")

    @staticmethod
    def fixture_svgo(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        # Keep real SVG files while isolating type checks from the SVGO installation.
        shutil.copyfile(command[command.index("-i") + 1], command[command.index("-o") + 1])
        return subprocess.CompletedProcess(command, 0, "", "")

    def batch(self) -> None:
        with redirect_stderr(io.StringIO()):
            assets.run_batch(
                assets.load_plan(self.plan), self.manifest,
                svgo_bin="fixture-svgo", runner=self.fixture_svgo,
            )

    def test_svg_batch_and_verify_keep_vector_type_without_raw_source(self) -> None:
        self.batch()
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest[0]["kind"], "svg")
        self.assertEqual((manifest[0]["width"], manifest[0]["height"], manifest[0]["aspectRatio"]), (24, 12, "2/1"))
        self.assertNotIn("alpha", manifest[0])
        self.source.unlink()
        self.assertTrue(assets.verify_plan(self.plan, self.manifest)["verified"])

    def test_plan_rejects_output_extensions_inconsistent_with_type(self) -> None:
        for kind, extension in (("svg", ".png"), ("image", ".svg"), ("video", ".webp")):
            with self.subTest(kind=kind):
                self.write_plan(kind=kind, outputPath=str(self.output.with_suffix(extension)))
                with self.assertRaisesRegex(RuntimeError, "TYPE_MISMATCH"):
                    assets.load_plan(self.plan)

    def test_invalid_svg_sources_do_not_publish_assets(self) -> None:
        sources = (
            b"\x89PNG\r\n\x1a\n",
            b'<html><svg width="24" height="12"/></html>',
            b'<svg width="24" height="12">',
        )
        for content in sources:
            with self.subTest(content=content):
                self.source.write_bytes(content)
                with self.assertRaisesRegex(RuntimeError, "TYPE_MISMATCH"):
                    self.batch()
                self.assertFalse(self.output.exists())
                self.assertFalse(self.manifest.exists())

    def test_verify_rejects_wrong_svg_metadata(self) -> None:
        self.batch()
        original = self.manifest.read_text(encoding="utf-8")
        for field, wrong in (("width", 999), ("height", 999), ("aspectRatio", "1/1")):
            with self.subTest(field=field):
                manifest = json.loads(original)
                manifest[0][field] = wrong
                self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "SVG dimensions differ"):
                    assets.verify_plan(self.plan, self.manifest)

    def test_verify_rejects_non_svg_content_even_with_updated_hash(self) -> None:
        self.batch()
        self.output.write_text('<html><svg width="24" height="12"/></html>', encoding="utf-8")
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest[0]["sha256"] = assets.sha256(self.output)
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "TYPE_MISMATCH"):
            assets.verify_plan(self.plan, self.manifest)

    def test_single_svg_rejects_wrong_extension_and_preserves_existing_output(self) -> None:
        output = self.output.with_suffix(".png")
        output.write_bytes(b"existing")
        with self.assertRaisesRegex(RuntimeError, "TYPE_MISMATCH"):
            assets.optimize_svg(self.source, output, svgo_bin="fixture-svgo", runner=self.fixture_svgo)
        self.assertEqual(output.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
