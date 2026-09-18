#!/usr/bin/env python3
"""Convert, optimize and inspect Figma assets with ffmpeg and SVGO."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


Runner = Callable[..., subprocess.CompletedProcess[str]]


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} not found; install FFmpeg and ensure {name} is on PATH")
    return path


def run(command: list[str], *, runner: Runner = subprocess.run) -> subprocess.CompletedProcess[str]:
    result = runner(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"command failed: {' '.join(command)}")
    return result


def ffprobe(path: Path, *, ffprobe_bin: str, runner: Runner = subprocess.run) -> dict[str, Any]:
    result = run([
        ffprobe_bin, "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ], runner=runner)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid ffprobe JSON for {path}: {exc}") from exc


def video_stream(probe: dict[str, Any]) -> dict[str, Any]:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    raise RuntimeError("asset has no video/image stream")


def dimensions(probe: dict[str, Any]) -> tuple[int, int]:
    stream = video_stream(probe)
    try:
        width, height = int(stream["width"]), int(stream["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("ffprobe did not return valid width/height") from exc
    if width <= 0 or height <= 0:
        raise RuntimeError("asset width/height must be positive")
    return width, height


def ratio(width: int, height: int) -> str:
    divisor = math.gcd(width, height)
    return f"{width // divisor}/{height // divisor}"


def has_alpha(probe: dict[str, Any]) -> bool:
    pixel_format = str(video_stream(probe).get("pix_fmt", "")).lower()
    return any(marker in pixel_format for marker in ("rgba", "bgra", "argb", "yuva", "gbrap", "pal8"))


def has_transparent_pixels(
    path: Path, *, ffmpeg_bin: str, runner: Runner = subprocess.run,
) -> bool:
    result = run([
        ffmpeg_bin, "-v", "info", "-i", str(path),
        "-vf", "alphaextract,signalstats,metadata=print", "-frames:v", "1",
        "-f", "null", "-",
    ], runner=runner)
    output = f"{result.stdout}\n{result.stderr}"
    marker = "lavfi.signalstats.YMIN="
    for line in output.splitlines():
        if marker in line:
            try:
                return float(line.split(marker, 1)[1].strip()) < 255
            except ValueError as exc:
                raise RuntimeError("invalid alpha statistics returned by ffmpeg") from exc
    raise RuntimeError("ffmpeg did not return alpha statistics")


def top_level_atoms(path: Path) -> list[tuple[str, int]]:
    atoms: list[tuple[str, int]] = []
    size_total = path.stat().st_size
    with path.open("rb") as handle:
        offset = 0
        while offset + 8 <= size_total:
            handle.seek(offset)
            header = handle.read(8)
            if len(header) != 8:
                break
            size32, kind = struct.unpack(">I4s", header)
            header_size = 8
            if size32 == 1:
                extended = handle.read(8)
                if len(extended) != 8:
                    break
                atom_size = struct.unpack(">Q", extended)[0]
                header_size = 16
            elif size32 == 0:
                atom_size = size_total - offset
            else:
                atom_size = size32
            if atom_size < header_size or offset + atom_size > size_total:
                break
            atoms.append((kind.decode("ascii", errors="replace"), offset))
            offset += atom_size
    return atoms


def is_faststart(path: Path) -> bool:
    offsets = dict(top_level_atoms(path))
    return "moov" in offsets and "mdat" in offsets and offsets["moov"] < offsets["mdat"]


def parse_hex_color(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6 or any(c not in "0123456789abcdefABCDEF" for c in text):
        raise RuntimeError(f"color must be a 6-digit hex value, got: {value}")
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def unbake_expression(sample: str, background: int) -> str:
    """Reverse canvas compositing for one channel: true = (baked - (1-a)*bg) / a."""
    return (
        f"if(eq(alpha(X,Y),0),0,if(eq(alpha(X,Y),255),{sample},"
        f"clip(({sample}-(1-alpha(X,Y)/255)*{background})/(alpha(X,Y)/255),0,255)))"
    )


def svg_root_tag(text: str) -> str:
    match = re.search(r"<svg\b[^>]*>", text)
    if match is None:
        raise RuntimeError("source does not contain an <svg> root element")
    return match.group(0)


def svg_dimensions(text: str) -> tuple[int, int]:
    tag = svg_root_tag(text)

    def attribute(name: str) -> str | None:
        found = re.search(rf'{name}\s*=\s*"([^"]*)"', tag) or re.search(
            rf"{name}\s*=\s*'([^']*)'", tag
        )
        return found.group(1) if found else None

    def parse_length(value: str | None) -> float | None:
        if value is None:
            return None
        try:
            length = float(re.sub(r"(?i)px$", "", value.strip()))
        except ValueError:
            return None
        return length if length > 0 else None

    width = parse_length(attribute("width"))
    height = parse_length(attribute("height"))
    if width is None or height is None:
        parts = (attribute("viewBox") or attribute("viewbox") or "").replace(",", " ").split()
        if len(parts) == 4:
            width = width if width is not None else parse_length(parts[2])
            height = height if height is not None else parse_length(parts[3])
    if width is None or height is None:
        raise RuntimeError("cannot determine SVG dimensions from width/height or viewBox")
    return round(width), round(height)


def optimize_svg(
    source: Path,
    output: Path,
    *,
    svgo_bin: str,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(f".{output.stem}.tmp{output.suffix}")
    try:
        run(
            [svgo_bin, "--multipass", "-i", str(source), "-o", str(temporary_output)],
            runner=runner,
        )
        if not temporary_output.is_file():
            raise RuntimeError("svgo did not produce an output file")
        width, height = svg_dimensions(temporary_output.read_text(encoding="utf-8"))
        os.replace(temporary_output, output)
    finally:
        if temporary_output.exists():
            temporary_output.unlink()
    print(
        f"svgo: {source.stat().st_size} -> {output.stat().st_size} bytes",
        file=sys.stderr,
    )
    return {
        "outputPath": str(output),
        "width": width,
        "height": height,
        "aspectRatio": ratio(width, height),
    }


def common_metadata(path: Path, probe: dict[str, Any]) -> dict[str, Any]:
    width, height = dimensions(probe)
    return {
        "outputPath": str(path),
        "width": width,
        "height": height,
        "aspectRatio": ratio(width, height),
    }


def convert_image(
    source: Path,
    output: Path,
    *,
    flattened: bool = False,
    lossless: bool = False,
    quality: int = 80,
    max_width: int = 0,
    alpha_mask: Path | None = None,
    unbake: tuple[int, int, int] | None = None,
    expect_alpha: bool = False,
    ffmpeg_bin: str,
    ffprobe_bin: str,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    source_probe = ffprobe(source, ffprobe_bin=ffprobe_bin, runner=runner)
    if unbake is not None and alpha_mask is None and not has_transparent_pixels(
        source, ffmpeg_bin=ffmpeg_bin, runner=runner,
    ):
        raise RuntimeError(
            "--unbake-color needs per-pixel alpha, but the source is fully opaque; "
            "provide --alpha-mask from an isolated screenshot"
        )
    use_lossless = (
        flattened or lossless or alpha_mask is not None or unbake is not None
        or has_alpha(source_probe)
    )
    source_width, _ = dimensions(source_probe)
    scale_filter = (
        f"scale={max_width}:-2:flags=lanczos" if max_width and source_width > max_width else ""
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(f".{output.stem}.tmp{output.suffix}")
    command = [ffmpeg_bin, "-y", "-i", str(source)]
    filter_complex = ""
    if alpha_mask is not None:
        if not alpha_mask.is_file():
            raise RuntimeError(f"alpha mask not found: {alpha_mask}")
        width, height = dimensions(source_probe)
        tail = "[merged]" if unbake is not None else ""
        filter_complex = (
            f"[1:v]alphaextract,scale={width}:{height}:flags=lanczos[alpha];"
            f"[0:v][alpha]alphamerge{tail}"
        )
        command += ["-i", str(alpha_mask)]
    if unbake is not None:
        geq = (
            f"format=rgba,geq="
            f"r='{unbake_expression('r(X,Y)', unbake[0])}':"
            f"g='{unbake_expression('g(X,Y)', unbake[1])}':"
            f"b='{unbake_expression('b(X,Y)', unbake[2])}':"
            f"a='alpha(X,Y)'"
        )
        source_label = "[merged]" if alpha_mask is not None else "[0:v]"
        filter_complex += f";{source_label}{geq}" if filter_complex else f"{source_label}{geq}"
    if scale_filter:
        if filter_complex:
            filter_complex += f",{scale_filter}"
        else:
            command += ["-vf", scale_filter]
    if filter_complex:
        command += ["-filter_complex", filter_complex]
    command += ["-c:v", "libwebp"]
    if use_lossless:
        command += ["-lossless", "1", "-compression_level", "6"]
    else:
        command += ["-quality", str(quality)]
    command += [str(temporary_output)]
    try:
        run(command, runner=runner)
        final_probe = ffprobe(temporary_output, ffprobe_bin=ffprobe_bin, runner=runner)
        if expect_alpha or alpha_mask is not None:
            if not has_alpha(final_probe):
                raise RuntimeError("expected transparent output, but the output has no alpha channel")
            if not has_transparent_pixels(temporary_output, ffmpeg_bin=ffmpeg_bin, runner=runner):
                raise RuntimeError("expected transparent output, but the alpha channel is fully opaque")
        os.replace(temporary_output, output)
    finally:
        if temporary_output.exists():
            temporary_output.unlink()
    return common_metadata(output, final_probe)


def convert_video(
    source: Path,
    output: Path,
    *,
    ffmpeg_bin: str,
    ffprobe_bin: str,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    source_probe = ffprobe(source, ffprobe_bin=ffprobe_bin, runner=runner)
    has_audio = any(s.get("codec_type") == "audio" for s in source_probe.get("streams", []))
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_bin, "-y", "-i", str(source),
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    ]
    command += ["-c:a", "aac", "-b:a", "128k"] if has_audio else ["-an"]
    command += [str(output)]
    run(command, runner=runner)

    final_probe = ffprobe(output, ffprobe_bin=ffprobe_bin, runner=runner)
    stream = video_stream(final_probe)
    if stream.get("codec_name") != "h264":
        raise RuntimeError(f"expected h264 video, got {stream.get('codec_name')}")
    if stream.get("pix_fmt") != "yuv420p":
        raise RuntimeError(f"expected yuv420p, got {stream.get('pix_fmt')}")
    if not is_faststart(output):
        raise RuntimeError("MP4 is not faststart: moov atom is not before mdat")
    return common_metadata(output, final_probe)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert Figma image/video assets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    image = subparsers.add_parser("image", help="Convert PNG/JPEG to WebP.")
    image.add_argument("source")
    image.add_argument("output")
    image.add_argument("--flattened", action="store_true", help="Use lossless WebP for text-composited exports.")
    image.add_argument("--lossless", action="store_true")
    image.add_argument("--quality", type=int, default=80)
    image.add_argument("--max-width", type=int, default=0, help="Downscale wider sources to this pixel width with lanczos before encoding; 0 keeps the source resolution.")
    image.add_argument("--alpha-mask", type=Path, help="Isolated PNG whose alpha channel replaces the export alpha; it is scaled to the source dimensions.")
    image.add_argument("--unbake-color", help="Hex color (e.g. 1e1e1e) that Figma baked into semi-transparent RGB; true colors are restored via true=(baked-(1-a)*bg)/a after the optional alpha-mask merge.")
    image.add_argument("--expect-alpha", action="store_true", help="Fail when the converted image has no transparent pixels.")

    svg = subparsers.add_parser("svg", help="Optimize an SVG with SVGO.")
    svg.add_argument("source")
    svg.add_argument("output")

    video = subparsers.add_parser("video", help="Convert a video to progressive MP4.")
    video.add_argument("source")
    video.add_argument("output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source, output = Path(args.source), Path(args.output)
    if not source.is_file():
        print(f"source not found: {source}", file=sys.stderr)
        return 2
    if source.resolve() == output.resolve():
        print("source and output must be different files", file=sys.stderr)
        return 2
    try:
        if args.command == "svg":
            svgo_bin = shutil.which("svgo")
            if not svgo_bin:
                raise RuntimeError(
                    "svgo not found; install it with `npm install -g svgo` and ensure it is on PATH"
                )
            result = optimize_svg(source, output, svgo_bin=svgo_bin)
        else:
            ffmpeg_bin = require_tool("ffmpeg")
            ffprobe_bin = require_tool("ffprobe")
            if args.command == "image":
                if not 1 <= args.quality <= 100:
                    raise RuntimeError("--quality must be between 1 and 100")
                if args.max_width < 0:
                    raise RuntimeError("--max-width must be a non-negative pixel width")
                unbake = parse_hex_color(args.unbake_color) if args.unbake_color else None
                result = convert_image(
                    source, output, flattened=args.flattened, lossless=args.lossless,
                    quality=args.quality, max_width=args.max_width,
                    alpha_mask=args.alpha_mask, unbake=unbake,
                    expect_alpha=args.expect_alpha,
                    ffmpeg_bin=ffmpeg_bin, ffprobe_bin=ffprobe_bin,
                )
            else:
                result = convert_video(
                    source, output, ffmpeg_bin=ffmpeg_bin, ffprobe_bin=ffprobe_bin,
                )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
