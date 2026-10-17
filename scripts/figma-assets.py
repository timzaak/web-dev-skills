#!/usr/bin/env python3
"""Convert, optimize and inspect Figma assets with ffmpeg, TinyPNG and SVGO.

Single assets convert via `image|svg|video`; `batch` consumes an assets-plan.json
whose image entries must declare `transparent`, enforces baked-canvas alpha masks
and atomically writes the asset manifest.
"""

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
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit


Runner = Callable[..., subprocess.CompletedProcess[str]]

TINIFY_HOST = "api.tinify.com"
KYZ_PROXY_DEFAULT = "http://127.0.0.1:8477"

# All TinyPNG traffic targets the loopback kyz credential proxy; never route it
# through a system HTTP proxy.
_LOOPBACK_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


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
    try:
        result = run([
            ffmpeg_bin, "-v", "info", "-i", str(path),
            "-vf", "alphaextract,signalstats,metadata=print", "-frames:v", "1",
            "-f", "null", "-",
        ], runner=runner)
    except RuntimeError:
        if path.suffix.lower() != ".webp":
            raise
        # Some FFmpeg builds reject valid lossy WebP alpha streams. Inspect
        # the actual pixels with libwebp through Pillow instead; encoding and
        # native dimension validation still use the normal asset pipeline.
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "FFmpeg could not inspect WebP alpha; install Pillow with "
                "`python -m pip install Pillow` and retry"
            ) from exc
        try:
            with Image.open(path) as image:
                image.load()
                if "A" not in image.getbands():
                    return False
                return image.getchannel("A").getextrema()[0] < 255
        except OSError as exc:
            raise RuntimeError(f"cannot decode WebP for alpha inspection: {path}") from exc
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


def kyz_proxy_token() -> str | None:
    state_dirs: list[Path] = []
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        state_dirs.append(Path(local_appdata) / "kyz" / "daemon")
    state_home = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    state_dirs.append(Path(state_home) / "kyz" / "daemon")
    for directory in state_dirs:
        try:
            token = (directory / "proxy.token").read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if token:
            return token
    return None


def tinify_error_text(status: int, body: bytes) -> str:
    detail = body[:200].decode("utf-8", errors="replace").strip()
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, ValueError):
        payload = None
    if isinstance(payload, dict):
        detail = f"{payload.get('error', 'unknown')}: {payload.get('message', '')}".rstrip(": ")
    hint = ""
    if status == 401:
        hint = " (check the kyz proxy token and the stored tinify basic credential)"
    elif status == 429:
        hint = " (TinyPNG monthly compression quota exhausted)"
    return f"TinyPNG returned HTTP {status}: {detail}{hint}"


def tinify_call(
    upstream_url: str,
    *,
    proxy: str,
    token: str | None,
    data: bytes | None = None,
) -> tuple[int, bytes]:
    target = urlsplit(upstream_url)
    base = urlsplit(proxy if "://" in proxy else f"http://{proxy}")
    headers = {"Host": target.netloc}
    if data is not None:
        headers["Content-Type"] = "application/octet-stream"
    if token:
        headers["x-kyz-proxy-token"] = token
    request = urllib.request.Request(
        urlunsplit((base.scheme, base.netloc, target.path, target.query, "")),
        data=data,
        headers=headers,
    )
    try:
        with _LOOPBACK_OPENER.open(request, timeout=300) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(tinify_error_text(exc.code, exc.read())) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"cannot reach the kyz credential proxy at {base.netloc} ({exc.reason}); "
            "run `kyz daemon status` and confirm the tinify rule listens on it"
        ) from exc


def tinify_compress(
    image: Path,
    destination: Path,
    *,
    proxy: str,
    token: str | None,
) -> None:
    status, body = tinify_call(
        f"https://{TINIFY_HOST}/shrink", proxy=proxy, token=token, data=image.read_bytes(),
    )
    if status != 201:
        raise RuntimeError(f"TinyPNG returned HTTP {status}, expected 201")
    try:
        output_url = json.loads(body)["output"]["url"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        preview = body[:200].decode("utf-8", errors="replace")
        raise RuntimeError(f"unexpected TinyPNG shrink response: {preview!r}") from exc
    status, body = tinify_call(output_url, proxy=proxy, token=token)
    if status != 200:
        raise RuntimeError(f"TinyPNG output download returned HTTP {status}")
    destination.write_bytes(body)


def alpha_filter_graph(
    source_probe: dict[str, Any],
    *,
    alpha_mask: Path | None,
    unbake: tuple[int, int, int] | None,
) -> tuple[list[str], str]:
    """Build alpha handling inputs and filter graph; both empty when no alpha work is needed."""
    if alpha_mask is None and unbake is None:
        return [], ""
    inputs: list[str] = []
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
        inputs += ["-i", str(alpha_mask)]
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
    return inputs, filter_complex


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
    tinypng_proxy: str = KYZ_PROXY_DEFAULT,
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
    # PNG sources (and anything needing alpha work) go: local transparency fixup
    # -> TinyPNG compression via the kyz credential proxy -> WebP at the
    # configured quality. --lossless remains available as an explicit override.
    use_tinypng = source.suffix.lower() == ".png" or alpha_mask is not None or unbake is not None
    use_lossless = lossless
    source_width, _ = dimensions(source_probe)
    scale_filter = (
        f"scale={max_width}:-2:flags=lanczos" if max_width and source_width > max_width else ""
    )
    alpha_inputs, alpha_graph = alpha_filter_graph(
        source_probe, alpha_mask=alpha_mask, unbake=unbake,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(f".{output.stem}.tmp{output.suffix}")
    processed_png = output.with_name(f".{output.stem}.tmp-processed.png")
    tinified_png = output.with_name(f".{output.stem}.tmp-tinified.png")
    try:
        if use_tinypng:
            upload_source = source
            if alpha_inputs or alpha_graph or scale_filter:
                upload_source = processed_png
                tail = ",".join(part for part in (scale_filter, "format=rgba") if part)
                preprocess = [ffmpeg_bin, "-y", "-i", str(source), *alpha_inputs]
                if alpha_graph:
                    preprocess += ["-filter_complex", f"{alpha_graph},{tail}"]
                else:
                    preprocess += ["-vf", tail]
                preprocess += [str(processed_png)]
                run(preprocess, runner=runner)
            tinify_compress(
                upload_source, tinified_png, proxy=tinypng_proxy, token=kyz_proxy_token(),
            )
            print(
                f"tinify: {upload_source.stat().st_size} -> {tinified_png.stat().st_size} bytes "
                f"via kyz proxy ({TINIFY_HOST})",
                file=sys.stderr,
            )
            command = [ffmpeg_bin, "-y", "-i", str(tinified_png)]
            if alpha_mask is not None or unbake is not None:
                # TinyPNG may quantize rare alpha values (even fully transparent
                # corners) into nonzero opacity. Keep its compressed RGB while
                # restoring the exact, already scaled alpha prepared above.
                command += [
                    "-i", str(processed_png), "-filter_complex",
                    "[1:v]alphaextract[alpha];[0:v][alpha]alphamerge",
                ]
            command += ["-c:v", "libwebp"]
            if use_lossless:
                command += ["-lossless", "1", "-compression_level", "6"]
            else:
                command += ["-quality", str(quality), "-compression_level", "6"]
            command += [str(temporary_output)]
            run(command, runner=runner)
        else:
            command = [ffmpeg_bin, "-y", "-i", str(source)]
            if scale_filter:
                command += ["-vf", scale_filter]
            command += ["-c:v", "libwebp"]
            if use_lossless:
                command += ["-lossless", "1", "-compression_level", "6"]
            else:
                command += ["-quality", str(quality)]
            command += [str(temporary_output)]
            run(command, runner=runner)
        final_probe = ffprobe(temporary_output, ffprobe_bin=ffprobe_bin, runner=runner)
        if expect_alpha or alpha_mask is not None:
            if not has_alpha(final_probe):
                raise RuntimeError("expected transparent output, but the output has no alpha channel")
            if not has_transparent_pixels(temporary_output, ffmpeg_bin=ffmpeg_bin, runner=runner):
                raise RuntimeError("expected transparent output, but the alpha channel is fully opaque")
        os.replace(temporary_output, output)
        mode = "lossless" if use_lossless else f"quality {quality}"
        print(
            f"webp: {source.stat().st_size} -> {output.stat().st_size} bytes ({mode})",
            file=sys.stderr,
        )
    finally:
        for temporary in (temporary_output, processed_png, tinified_png):
            if temporary.exists():
                temporary.unlink()
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


PLAN_KINDS = ("image", "svg", "video")
PLAN_ENTRY_FIELDS = {"id", "name", "kind", "source", "outputPath", "publicUrl", "origin"}
IMAGE_ONLY_FIELDS = {
    "transparent", "alphaMask", "unbakeColor", "lossless", "quality", "maxWidth", "flattened",
}


def plan_entry_error(index: int, entry: dict[str, Any], message: str) -> RuntimeError:
    identity = entry.get("id") or entry.get("name") or f"#{index}"
    return RuntimeError(f"plan entry {identity}: {message}")


def load_plan(path: Path) -> list[dict[str, Any]]:
    """Parse and validate the asset plan; per-image transparency must be declared explicitly."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read asset plan {path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise RuntimeError("asset plan must be an object with an 'entries' array")
    entries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_outputs: set[str] = set()
    for index, raw in enumerate(payload["entries"]):
        if not isinstance(raw, dict):
            raise RuntimeError(f"plan entry #{index} must be an object")
        for field in ("id", "name", "kind", "source", "outputPath"):
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                raise plan_entry_error(index, raw, f"'{field}' must be a non-empty string")
        identity = raw["id"]
        if identity in seen_ids:
            raise plan_entry_error(index, raw, f"duplicate id: {identity}")
        seen_ids.add(identity)
        output_key = os.path.normcase(str(Path(raw["outputPath"]).resolve()))
        if output_key in seen_outputs:
            raise plan_entry_error(index, raw, f"duplicate outputPath: {raw['outputPath']}")
        seen_outputs.add(output_key)
        kind = raw["kind"]
        if kind not in PLAN_KINDS:
            raise plan_entry_error(
                index, raw, f"'kind' must be one of {', '.join(PLAN_KINDS)}; got {kind}",
            )
        unknown = set(raw) - PLAN_ENTRY_FIELDS - IMAGE_ONLY_FIELDS
        if unknown:
            raise plan_entry_error(index, raw, f"unknown field(s): {', '.join(sorted(unknown))}")
        entry: dict[str, Any] = {
            "id": identity,
            "name": raw["name"],
            "kind": kind,
            "origin": raw.get("origin", "download-assets"),
            "source": Path(raw["source"]),
            "output": Path(raw["outputPath"]),
            "publicUrl": raw.get("publicUrl"),
            "flattened": bool(raw.get("flattened", False)),
        }
        if kind == "video" and not entry["publicUrl"]:
            raise plan_entry_error(index, raw, "'publicUrl' is required for video entries")
        if kind == "image":
            transparent = raw.get("transparent")
            if not isinstance(transparent, bool):
                raise plan_entry_error(
                    index, raw, "'transparent' must be declared as true or false for image entries",
                )
            quality = raw.get("quality", 80)
            if isinstance(quality, bool) or not isinstance(quality, int) or not 1 <= quality <= 100:
                raise plan_entry_error(index, raw, "'quality' must be an integer between 1 and 100")
            max_width = raw.get("maxWidth", 0)
            if isinstance(max_width, bool) or not isinstance(max_width, int) or max_width < 0:
                raise plan_entry_error(index, raw, "'maxWidth' must be a non-negative integer")
            alpha_mask = raw.get("alphaMask")
            if alpha_mask is not None and not isinstance(alpha_mask, str):
                raise plan_entry_error(index, raw, "'alphaMask' must be a path string")
            unbake = raw.get("unbakeColor")
            if unbake is not None:
                if not isinstance(unbake, str):
                    raise plan_entry_error(index, raw, "'unbakeColor' must be a hex string like 1e1e1e")
                try:
                    unbake = parse_hex_color(unbake)
                except RuntimeError as exc:
                    raise plan_entry_error(index, raw, str(exc)) from exc
            entry.update({
                "transparent": transparent,
                "alpha_mask": Path(alpha_mask) if alpha_mask else None,
                "unbake": unbake,
                "lossless": bool(raw.get("lossless", False)),
                "quality": quality,
                "max_width": max_width,
            })
        else:
            for field in IMAGE_ONLY_FIELDS:
                if field in raw:
                    raise plan_entry_error(index, raw, f"'{field}' only applies to image entries")
        entries.append(entry)
    return entries


def validate_alpha_declaration(
    entry: dict[str, Any],
    *,
    ffmpeg_bin: str,
    ffprobe_bin: str,
    runner: Runner = subprocess.run,
) -> str | None:
    """Enforce a transparent declaration against the source pixels.

    Fully opaque sources declared transparent require an isolated-screenshot
    mask. Inspection errors propagate without being treated as missing alpha.
    Returns a warning for an opaque declaration with real transparent pixels.
    """
    source: Path = entry["source"]
    source_has_alpha = has_alpha(ffprobe(source, ffprobe_bin=ffprobe_bin, runner=runner))
    pixel_alpha = source_has_alpha and has_transparent_pixels(
        source, ffmpeg_bin=ffmpeg_bin, runner=runner,
    )
    if entry["transparent"]:
        if not pixel_alpha and entry["alpha_mask"] is None:
            raise RuntimeError(
                f"plan entry {entry['id']}: ALPHA_MASK_REQUIRED: declared transparent, "
                "but the source has no transparent pixels. Call "
                "get_screenshot(contentsOnly: true) for the node, save the isolated PNG "
                "under raw/ and reference it via the entry's alphaMask"
            )
        return None
    if pixel_alpha:
        return (
            f"plan entry {entry['id']} is declared opaque, but the source has transparent "
            "pixels; review the declaration and set transparent to true if intended"
        )
    return None


def write_manifest(manifest_path: Path, manifest_entries: list[dict[str, Any]]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest_path.with_name(f".{manifest_path.stem}.tmp{manifest_path.suffix}")
    temporary.write_text(
        json.dumps(manifest_entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    os.replace(temporary, manifest_path)


def run_batch(
    entries: list[dict[str, Any]],
    manifest_path: Path,
    *,
    tinypng_proxy: str = KYZ_PROXY_DEFAULT,
    overwrite_existing: bool = False,
    ffmpeg_bin: str = "",
    ffprobe_bin: str = "",
    svgo_bin: str | None = None,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    for entry in entries:
        if not entry["source"].is_file():
            raise RuntimeError(f"plan entry {entry['id']}: source not found: {entry['source']}")
        alpha_mask = entry.get("alpha_mask")
        if alpha_mask is not None and not alpha_mask.is_file():
            raise RuntimeError(f"plan entry {entry['id']}: alphaMask not found: {alpha_mask}")
        if entry["output"].exists() and not overwrite_existing:
            raise RuntimeError(
                f"plan entry {entry['id']}: output already exists: {entry['output']}; "
                "use --overwrite-existing to replace outputs from an earlier batch run"
            )
    warnings: list[dict[str, str]] = []
    for entry in entries:
        if entry["kind"] != "image":
            continue
        warning = validate_alpha_declaration(
            entry, ffmpeg_bin=ffmpeg_bin, ffprobe_bin=ffprobe_bin, runner=runner,
        )
        if warning:
            print(f"batch warning: {warning}", file=sys.stderr)
            warnings.append({"id": entry["id"], "message": warning})
    manifest_entries: list[dict[str, Any]] = []
    total = len(entries)
    for index, entry in enumerate(entries, start=1):
        print(
            f"batch: [{index}/{total}] {entry['id']} ({entry['kind']}) -> {entry['output']}",
            file=sys.stderr,
        )
        if entry["kind"] == "image":
            result = convert_image(
                entry["source"], entry["output"],
                flattened=entry["flattened"], lossless=entry["lossless"],
                quality=entry["quality"], max_width=entry["max_width"],
                alpha_mask=entry["alpha_mask"], unbake=entry["unbake"],
                expect_alpha=entry["transparent"], tinypng_proxy=tinypng_proxy,
                ffmpeg_bin=ffmpeg_bin, ffprobe_bin=ffprobe_bin, runner=runner,
            )
        elif entry["kind"] == "svg":
            if svgo_bin is None:
                raise RuntimeError(
                    "svgo not found; install it with `npm install -g svgo` and ensure it is on PATH"
                )
            result = optimize_svg(entry["source"], entry["output"], svgo_bin=svgo_bin, runner=runner)
        else:
            result = convert_video(
                entry["source"], entry["output"], ffmpeg_bin=ffmpeg_bin, ffprobe_bin=ffprobe_bin,
                runner=runner,
            )
        manifest_entry: dict[str, Any] = {
            "id": entry["id"],
            "name": entry["name"],
            "kind": entry["kind"],
            "source": entry["origin"],
        }
        if entry["flattened"]:
            manifest_entry["flattened"] = True
        if entry["kind"] == "image":
            manifest_entry["transparent"] = entry["transparent"]
        manifest_entry["outputPath"] = result["outputPath"]
        if entry["publicUrl"]:
            manifest_entry["publicUrl"] = entry["publicUrl"]
        manifest_entry.update({
            key: result[key] for key in ("width", "height", "aspectRatio")
        })
        manifest_entries.append(manifest_entry)
    write_manifest(manifest_path, manifest_entries)
    return {"manifestPath": str(manifest_path), "total": total, "warnings": warnings}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert Figma image/video assets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    image = subparsers.add_parser("image", help="Convert PNG/JPEG to WebP.")
    image.add_argument("source")
    image.add_argument("output")
    image.add_argument("--flattened", action="store_true", help="Mark text-composited exports; quality 80 is used by default. Use --lossless to preserve exact pixels.")
    image.add_argument("--lossless", action="store_true")
    image.add_argument("--quality", type=int, default=80)
    image.add_argument("--max-width", type=int, default=0, help="Downscale wider sources to this pixel width with lanczos before encoding; 0 keeps the source resolution.")
    image.add_argument("--alpha-mask", type=Path, help="Isolated PNG whose alpha channel replaces the export alpha; it is scaled to the source dimensions.")
    image.add_argument("--unbake-color", help="Hex color (e.g. 1e1e1e) that Figma baked into semi-transparent RGB; true colors are restored via true=(baked-(1-a)*bg)/a after the optional alpha-mask merge.")
    image.add_argument("--expect-alpha", action="store_true", help="Fail when the converted image has no transparent pixels.")
    image.add_argument(
        "--tinypng-proxy",
        default=KYZ_PROXY_DEFAULT,
        help=f"Base URL of the kyz credential proxy used to reach TinyPNG (default: {KYZ_PROXY_DEFAULT}). PNG sources always compress through TinyPNG before WebP encoding.",
    )

    svg = subparsers.add_parser("svg", help="Optimize an SVG with SVGO.")
    svg.add_argument("source")
    svg.add_argument("output")

    video = subparsers.add_parser("video", help="Convert a video to progressive MP4.")
    video.add_argument("source")
    video.add_argument("output")

    batch = subparsers.add_parser(
        "batch",
        help="Convert every plan entry and atomically write the asset manifest; "
        "image entries must declare transparent true/false and baked-canvas sources "
        "must come with an alphaMask.",
    )
    batch.add_argument("plan", help="Path to assets-plan.json; relative paths inside resolve against the current directory.")
    batch.add_argument(
        "--manifest", type=Path, default=None,
        help="Manifest output path; defaults to assets-manifest.json next to the plan.",
    )
    batch.add_argument("--tinypng-proxy", default=KYZ_PROXY_DEFAULT, help=f"Base URL of the kyz credential proxy used to reach TinyPNG (default: {KYZ_PROXY_DEFAULT}).")
    batch.add_argument(
        "--overwrite-existing", action="store_true",
        help="Replace outputs left by an earlier batch run; never use it to bypass review.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result: dict[str, Any]
        if args.command == "batch":
            plan_path = Path(args.plan)
            if not plan_path.is_file():
                print(f"plan not found: {plan_path}", file=sys.stderr)
                return 2
            manifest_path = args.manifest or plan_path.parent / "assets-manifest.json"
            entries = load_plan(plan_path)
            needs_av_tools = any(entry["kind"] in ("image", "video") for entry in entries)
            result = run_batch(
                entries, manifest_path,
                tinypng_proxy=args.tinypng_proxy,
                overwrite_existing=args.overwrite_existing,
                ffmpeg_bin=require_tool("ffmpeg") if needs_av_tools else "",
                ffprobe_bin=require_tool("ffprobe") if needs_av_tools else "",
                svgo_bin=shutil.which("svgo"),
            )
        else:
            source, output = Path(args.source), Path(args.output)
            if not source.is_file():
                print(f"source not found: {source}", file=sys.stderr)
                return 2
            if source.resolve() == output.resolve():
                print("source and output must be different files", file=sys.stderr)
                return 2
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
                        expect_alpha=args.expect_alpha, tinypng_proxy=args.tinypng_proxy,
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
