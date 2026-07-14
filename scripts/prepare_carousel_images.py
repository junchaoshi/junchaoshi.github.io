#!/usr/bin/env python3
"""Generate responsive JPEG derivatives for homepage carousel images.

Typical workflow:
  1. Put the full-size carousel image in assets/img/main_page/.
  2. Reference only the original image in _pages/about.md:
       - image: assets/img/main_page/my_slide.jpg
  3. Run:
       python scripts/prepare_carousel_images.py

The script reads carousel image paths from _pages/about.md and generates the
JPEG files expected by _includes/carousel.html, for example:
  my_slide-480.jpg
  my_slide-640.jpg
  my_slide-800.jpg
  my_slide-1400.jpg

It preserves color profiles by converting to sRGB, keeps the original aspect
ratio unless an output aspect ratio is requested, and refuses to treat existing
*-WIDTH.jpg derivatives as source images.

By default the output is center-cropped to 2:1, matching the homepage carousel
container and the 1400x700 image dimensions declared in the template.
"""

from __future__ import annotations

import argparse
import re
import sys
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image, ImageCms, ImageOps
except ImportError:  # pragma: no cover - depends on local environment
    print("This script requires Pillow. Install it with: python -m pip install pillow", file=sys.stderr)
    raise SystemExit(1)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGE = ROOT / "_pages" / "about.md"
DEFAULT_WIDTHS = (480, 640, 800, 1400)
LOCAL_IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
WIDTH_DERIVATIVE_RE = re.compile(r"^(?P<base>.+)-(?P<width>[1-9]\d{1,4})$")
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*", re.DOTALL)
CAROUSEL_IMAGE_RE = re.compile(r"(?m)^\s*-\s*image:\s*(?P<value>.+?)\s*$")


def parse_widths(raw_widths: list[int]) -> tuple[int, ...]:
    widths = tuple(sorted(set(raw_widths)))
    if not widths:
        raise argparse.ArgumentTypeError("at least one width is required")
    for width in widths:
        if width < 1:
            raise argparse.ArgumentTypeError("widths must be positive integers")
    return widths


def parse_aspect_ratio(value: str) -> tuple[int, int] | None:
    if value.lower() in {"none", "original", "auto"}:
        return None
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*[:/]\s*(\d+(?:\.\d+)?)\s*", value)
    if not match:
        raise argparse.ArgumentTypeError("--aspect must look like 2:1, 16:9, or none")
    width = float(match.group(1))
    height = float(match.group(2))
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("--aspect values must be positive")
    return int(round(width * 1000)), int(round(height * 1000))


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def carousel_images_from_page(page: Path) -> list[str]:
    text = page.read_text(encoding="utf-8")
    front_matter = FRONT_MATTER_RE.match(text)
    if not front_matter:
        raise ValueError(f"{page.relative_to(ROOT)} has no YAML front matter")

    images: list[str] = []
    for match in CAROUSEL_IMAGE_RE.finditer(front_matter.group("body")):
        value = strip_yaml_scalar(match.group("value"))
        if value and "://" not in value:
            images.append(value)
    return images


def resolve_site_path(value: str) -> Path:
    path = Path(value.lstrip("/"))
    if path.is_absolute():
        return path
    return ROOT / path


def site_relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def width_derivative(path: Path) -> tuple[str, int] | None:
    match = WIDTH_DERIVATIVE_RE.match(path.stem)
    if not match:
        return None
    return match.group("base"), int(match.group("width"))


def find_original_for_derivative(path: Path) -> Path | None:
    derivative = width_derivative(path)
    if not derivative:
        return None

    base, _width = derivative
    candidates = [path.with_name(f"{base}{extension}") for extension in sorted(LOCAL_IMAGE_EXTENSIONS)]
    for candidate in candidates:
        if candidate != path and candidate.exists():
            return candidate
    return None


def canonical_source(path: Path) -> tuple[Path | None, str | None]:
    if not width_derivative(path):
        return path, None

    original = find_original_for_derivative(path)
    if original:
        return original, f"{path.name} looks like a generated derivative; using {original.name}"
    return None, f"{path.name} looks like a generated derivative, but no original image was found"


def to_srgb(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    icc = image.info.get("icc_profile")
    has_alpha = image.mode in {"LA", "RGBA"} or ("transparency" in image.info)
    output_mode = "RGBA" if has_alpha else "RGB"

    if icc:
        try:
            source_profile = ImageCms.ImageCmsProfile(BytesIO(icc))
            target_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
            return ImageCms.profileToProfile(image, source_profile, target_profile, outputMode=output_mode)
        except Exception:
            pass

    if image.mode != output_mode:
        return image.convert(output_mode)
    return image


def flatten_to_rgb(image: Image.Image, background: tuple[int, int, int]) -> Image.Image:
    if image.mode == "RGB":
        return image
    if image.mode in {"RGBA", "LA"}:
        rgba = image.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, background)
        canvas.paste(rgba, mask=rgba.getchannel("A"))
        return canvas
    return image.convert("RGB")


def crop_to_aspect(image: Image.Image, aspect: tuple[int, int] | None) -> Image.Image:
    if aspect is None:
        return image

    aspect_width, aspect_height = aspect
    target_ratio = aspect_width / aspect_height
    current_ratio = image.width / image.height

    if abs(current_ratio - target_ratio) < 0.001:
        return image

    if current_ratio > target_ratio:
        crop_width = round(image.height * target_ratio)
        left = max(0, (image.width - crop_width) // 2)
        return image.crop((left, 0, left + crop_width, image.height))

    crop_height = round(image.width / target_ratio)
    top = max(0, (image.height - crop_height) // 2)
    return image.crop((0, top, image.width, top + crop_height))


def resized_dimensions(width: int, height: int, target_width: int, *, allow_upscale: bool) -> tuple[int, int]:
    output_width = target_width if allow_upscale else min(width, target_width)
    output_height = max(1, round(height * output_width / width))
    return output_width, output_height


def target_for(source: Path, width: int) -> Path:
    return source.with_name(f"{source.stem}-{width}.jpg")


def prepare_image(source: Path, args: argparse.Namespace) -> tuple[int, int]:
    if source.suffix.lower() not in LOCAL_IMAGE_EXTENSIONS:
        print(f"skip {site_relative(source)}: unsupported image type")
        return 0, 0

    generated = 0
    warnings = 0
    with Image.open(source) as image:
        image = crop_to_aspect(flatten_to_rgb(to_srgb(image), args.background), args.aspect)
        for width in args.widths:
            target = target_for(source, width)
            output_width, output_height = resized_dimensions(
                image.width,
                image.height,
                width,
                allow_upscale=args.allow_upscale,
            )
            if output_width != width:
                warnings += 1
                print(
                    f"warn {site_relative(source)}: source is {image.width}px wide; "
                    f"{target.name} will be {output_width}px wide without upscaling"
                )

            if target.exists() and not args.force:
                continue

            generated += 1
            action = "would generate" if args.dry_run else "generated"
            print(f"{action} {site_relative(target)} ({output_width}x{output_height})")
            if args.dry_run:
                continue

            resized = image.resize((output_width, output_height), Image.Resampling.LANCZOS)
            target.parent.mkdir(parents=True, exist_ok=True)
            resized.save(
                target,
                format="JPEG",
                quality=args.quality,
                optimize=True,
                progressive=True,
                subsampling=args.subsampling,
            )

    return generated, warnings


def clean_extra_derivatives(sources: list[Path], args: argparse.Namespace) -> int:
    source_dirs = {source.parent for source in sources}
    expected = {target_for(source, width).resolve() for source in sources for width in args.widths}
    removed = 0

    for directory in sorted(source_dirs):
        for candidate in sorted(directory.glob("*.jpg")):
            if not width_derivative(candidate):
                continue
            if candidate.resolve() in expected:
                continue
            removed += 1
            action = "would remove" if args.dry_run else "removed"
            print(f"{action} unused carousel derivative {site_relative(candidate)}")
            if not args.dry_run:
                candidate.unlink()

    return removed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path, default=DEFAULT_PAGE, help="Page containing carousel front matter.")
    parser.add_argument("--widths", nargs="+", type=int, default=list(DEFAULT_WIDTHS), help="Generated JPEG widths.")
    parser.add_argument(
        "--aspect",
        type=parse_aspect_ratio,
        default=parse_aspect_ratio("2:1"),
        help="Center-crop output to this ratio. Use none to preserve the original aspect ratio.",
    )
    parser.add_argument("--quality", type=int, default=88, help="JPEG quality, 1-100.")
    parser.add_argument(
        "--subsampling",
        type=int,
        default=0,
        choices=(0, 1, 2),
        help="JPEG chroma subsampling. 0 preserves color best; 2 gives smaller files.",
    )
    parser.add_argument(
        "--background",
        default="255,255,255",
        help="RGB background for transparent images, such as 255,255,255.",
    )
    parser.add_argument("--allow-upscale", action="store_true", help="Allow upscaling images smaller than a target width.")
    parser.add_argument("--force", action="store_true", help="Regenerate JPEG files even when they already exist.")
    parser.add_argument("--dry-run", action="store_true", help="Report actions without writing files.")
    parser.add_argument(
        "--clean-extra",
        action="store_true",
        help="Remove unused *-WIDTH.jpg derivatives in carousel image directories.",
    )
    args = parser.parse_args()

    args.widths = parse_widths(args.widths)
    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")

    try:
        args.background = tuple(int(part.strip()) for part in args.background.split(","))
    except ValueError:
        parser.error("--background must be three comma-separated integers")
    if len(args.background) != 3 or any(channel < 0 or channel > 255 for channel in args.background):
        parser.error("--background must be three RGB values between 0 and 255")

    if not args.page.is_absolute():
        args.page = ROOT / args.page
    return args


def main() -> int:
    args = parse_args()
    if not args.page.exists():
        print(f"missing page: {args.page}", file=sys.stderr)
        return 1

    try:
        image_values = carousel_images_from_page(args.page)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    if not image_values:
        print(f"no carousel images found in {site_relative(args.page)}")
        return 0

    sources: list[Path] = []
    for value in image_values:
        source = resolve_site_path(value)
        if not source.exists():
            print(f"skip {value}: missing source image")
            continue

        source, note = canonical_source(source)
        if note:
            if source is None:
                print(f"skip {value}: {note}")
                continue
            print(f"{value}: {note}")
        sources.append(source)

    generated = 0
    warnings = 0
    for source in sources:
        image_generated, image_warnings = prepare_image(source, args)
        generated += image_generated
        warnings += image_warnings

    removed = 0
    if args.clean_extra:
        removed = clean_extra_derivatives(sources, args)

    mode = "dry run: " if args.dry_run else ""
    print(
        f"{mode}{len(sources)} source images checked, "
        f"{generated} derivatives generated, {removed} derivatives removed, {warnings} warnings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
