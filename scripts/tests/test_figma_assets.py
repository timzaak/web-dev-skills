from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("figma_assets", REPO_ROOT / "scripts" / "figma-assets.py")
assert SPEC and SPEC.loader
figma_assets = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = figma_assets
SPEC.loader.exec_module(figma_assets)


class FakeCompleted:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class MetadataTests(unittest.TestCase):
    def test_ratio_is_reduced(self) -> None:
        self.assertEqual(figma_assets.ratio(1920, 1080), "16/9")

    def test_alpha_pixel_formats(self) -> None:
        self.assertTrue(figma_assets.has_alpha({"streams": [{"codec_type": "video", "pix_fmt": "rgba"}]}))
        self.assertFalse(figma_assets.has_alpha({"streams": [{"codec_type": "video", "pix_fmt": "yuv420p"}]}))

    def test_dimensions_reject_missing_stream(self) -> None:
        with self.assertRaises(RuntimeError):
            figma_assets.dimensions({"streams": []})


class AtomTests(unittest.TestCase):
    @staticmethod
    def atom(kind: bytes, payload: bytes = b"") -> bytes:
        return (8 + len(payload)).to_bytes(4, "big") + kind + payload

    def test_faststart_when_moov_precedes_mdat(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "v.mp4"
            path.write_bytes(self.atom(b"ftyp") + self.atom(b"moov") + self.atom(b"mdat"))
            self.assertTrue(figma_assets.is_faststart(path))

    def test_not_faststart_when_mdat_precedes_moov(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "v.mp4"
            path.write_bytes(self.atom(b"ftyp") + self.atom(b"mdat") + self.atom(b"moov"))
            self.assertFalse(figma_assets.is_faststart(path))


class CommandConstructionTests(unittest.TestCase):
    def test_flattened_image_uses_lossless(self) -> None:
        calls: list[list[str]] = []

        def runner(command, **kwargs):
            calls.append(command)
            if command[0] == "probe":
                return FakeCompleted(stdout=json.dumps({"streams": [{"codec_type": "video", "width": 10, "height": 5, "pix_fmt": "rgb24"}]}))
            Path(command[-1]).write_bytes(b"webp")
            return FakeCompleted()

        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "a.png"
            source.write_bytes(b"png")
            output = Path(temp) / "a.webp"
            result = figma_assets.convert_image(
                source, output, flattened=True, ffmpeg_bin="ffmpeg", ffprobe_bin="probe", runner=runner,
            )
        ffmpeg_call = next(call for call in calls if call[0] == "ffmpeg")
        self.assertIn("-lossless", ffmpeg_call)
        self.assertEqual(result["conversion"]["mode"], "webp-lossless")

    def test_photo_uses_quality_100(self) -> None:
        calls: list[list[str]] = []

        def runner(command, **kwargs):
            calls.append(command)
            if command[0] == "probe":
                return FakeCompleted(stdout=json.dumps({"streams": [{"codec_type": "video", "width": 16, "height": 9, "pix_fmt": "rgb24"}]}))
            Path(command[-1]).write_bytes(b"webp")
            return FakeCompleted()

        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "a.jpg"
            source.write_bytes(b"jpg")
            figma_assets.convert_image(source, Path(temp) / "a.webp", ffmpeg_bin="ffmpeg", ffprobe_bin="probe", runner=runner)
        ffmpeg_call = next(call for call in calls if call[0] == "ffmpeg")
        self.assertEqual(ffmpeg_call[ffmpeg_call.index("-quality") + 1], "100")


if __name__ == "__main__":
    unittest.main()
