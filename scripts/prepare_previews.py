#!/usr/bin/env python3
"""Generate optimized publication preview images and BibTeX dimensions.

Typical workflow:
  1. Put the original cover image in assets/img/publication_preview/.
  2. Add only this field to the BibTeX entry:
       preview={my_cover.png},
  3. Run:
       python scripts/prepare_previews.py
     To scan all bibliography files:
       python scripts/prepare_previews.py --all
     To remove old unreferenced *-WIDTH.webp derivatives:
       python scripts/prepare_previews.py --all --clean-derived

The script generates my_cover-350.webp, updates preview to that WebP file,
and adds preview_width / preview_height automatically. If a BibTeX entry
accidentally points to a generated derivative such as my_cover-480.jpg or
my_cover-300.webp, the script will prefer the original my_cover.jpg/png and
normalize the entry back to the canonical -350.webp preview.
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
DEFAULT_BIB = ROOT / "_bibliography" / "papers.bib"
DEFAULT_PREVIEW_DIR = ROOT / "assets" / "img" / "publication_preview"
DEFAULT_MAX_WIDTH = 350
LOCAL_IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff"}
PASSTHROUGH_IMAGE_EXTENSIONS = {".gif", ".webp"}
WIDTH_DERIVATIVE_RE = re.compile(r"^(?P<base>.+)-(?P<width>[1-9]\d{1,4})$")


def entry_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"(?m)^@\w+\s*\{", text):
        depth = 0
        started = False
        for index in range(match.start(), len(text)):
            char = text[index]
            if char == "{":
                depth += 1
                started = True
            elif char == "}":
                depth -= 1
                if started and depth == 0:
                    spans.append((match.start(), index + 1))
                    break
    return spans


def entry_key(entry: str) -> str:
    match = re.match(r"(?s)@\w+\s*\{\s*([^,\s]+)", entry)
    return match.group(1) if match else "<unknown>"


def field_pattern(field: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?im)^([ \t]*){re.escape(field)}\s*=\s*(?:\{{([^}}]*)\}}|\"([^\"]*)\"|([^,\n]*))\s*,?\s*$"
    )


def get_field(entry: str, field: str) -> str | None:
    match = field_pattern(field).search(entry)
    if not match:
        return None
    return next(value for value in match.groups()[1:] if value is not None).strip()


def set_field(entry: str, field: str, value: str, *, after: str = "preview") -> tuple[str, bool]:
    pattern = field_pattern(field)
    match = pattern.search(entry)
    if match:
        old = match.group(0)
        replacement = f"{match.group(1)}{field}={{{value}}},"
        if old == replacement:
            return entry, False
        return entry[: match.start()] + replacement + entry[match.end() :], True

    after_match = field_pattern(after).search(entry)
    if after_match:
        indent = after_match.group(1)
        insertion = f"\n{indent}{field}={{{value}}},"
        return entry[: after_match.end()] + insertion + entry[after_match.end() :], True

    close = entry.rfind("}")
    if close == -1:
        return entry, False
    insertion = f"  {field}={{{value}}},\n"
    return entry[:close] + insertion + entry[close:], True


def resolve_preview_path(value: str, preview_dir: Path) -> Path | None:
    if "://" in value:
        return None
    raw = value.strip()
    path = Path(raw.lstrip("/"))
    if path.is_absolute():
        return path
    if len(path.parts) > 1:
        return ROOT / path
    return preview_dir / path


def preview_value_for(path: Path, preview_dir: Path) -> str:
    try:
        return path.relative_to(preview_dir).as_posix()
    except ValueError:
        return path.relative_to(ROOT).as_posix()


def width_derivative(path: Path) -> tuple[str, int] | None:
    match = WIDTH_DERIVATIVE_RE.match(path.stem)
    if not match:
        return None
    return match.group("base"), int(match.group("width"))


def is_canonical_preview(path: Path, max_width: int) -> bool:
    derivative = width_derivative(path)
    return path.suffix.lower() == ".webp" and derivative is not None and derivative[1] == max_width


def find_original_for_derivative(path: Path, preview_dir: Path) -> Path | None:
    derivative = width_derivative(path)
    if not derivative:
        return None

    base, _width = derivative
    search_dir = path.parent if path.parent != Path(".") else preview_dir
    preferred_exts = [path.suffix.lower()]
    preferred_exts.extend(sorted(LOCAL_IMAGE_EXTENSIONS))
    preferred_exts.extend(sorted(PASSTHROUGH_IMAGE_EXTENSIONS))

    seen: set[str] = set()
    for extension in preferred_exts:
        if extension in seen:
            continue
        seen.add(extension)
        candidate = search_dir / f"{base}{extension}"
        if candidate != path and candidate.exists():
            return candidate
    return None


def canonical_source_for(source: Path, preview_dir: Path, max_width: int) -> tuple[Path | None, str | None]:
    if is_canonical_preview(source, max_width):
        return source, None

    if width_derivative(source):
        original = find_original_for_derivative(source, preview_dir)
        if original:
            return original, f"{source.name} looks like a generated derivative; using {original.name}"
        return None, f"{source.name} looks like a generated derivative, but no original image was found"

    return source, None


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


def resized_dimensions(width: int, height: int, max_width: int) -> tuple[int, int]:
    target_width = min(width, max_width)
    target_height = max(1, round(height * target_width / width))
    return target_width, target_height


def prepare_image(
    source: Path,
    *,
    max_width: int,
    quality: int,
    force: bool,
    dry_run: bool,
) -> tuple[Path, int, int, bool]:
    suffix = source.suffix.lower()
    if suffix in PASSTHROUGH_IMAGE_EXTENSIONS:
        with Image.open(source) as image:
            width, height = image.size
        return source, width, height, False

    if suffix not in LOCAL_IMAGE_EXTENSIONS:
        raise ValueError(f"unsupported preview image type: {source.name}")

    target = source.with_name(f"{source.stem}-{max_width}.webp")
    with Image.open(source) as image:
        image = to_srgb(image)
        width, height = resized_dimensions(image.width, image.height, max_width)
        generated = force or not target.exists()
        if generated and not dry_run:
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(target, format="WEBP", quality=quality, method=6)
    return target, width, height, generated


def process_bib(path: Path, preview_dir: Path, args: argparse.Namespace) -> tuple[int, int, set[Path]]:
    text = path.read_text(encoding="utf-8")
    spans = entry_spans(text)
    rebuilt: list[str] = []
    cursor = 0
    changed_entries = 0
    generated_images = 0
    referenced_previews: set[Path] = set()

    for start, end in spans:
        rebuilt.append(text[cursor:start])
        entry = text[start:end]
        key = entry_key(entry)
        preview = get_field(entry, "preview")
        if not preview:
            rebuilt.append(entry)
            cursor = end
            continue

        source = resolve_preview_path(preview, preview_dir)
        if source is None:
            print(f"skip {path.name}:{key}: remote preview cannot be measured")
            rebuilt.append(entry)
            cursor = end
            continue
        if not source.exists():
            print(f"skip {path.name}:{key}: missing {source}")
            rebuilt.append(entry)
            cursor = end
            continue

        source, source_note = canonical_source_for(source, preview_dir, args.max_width)
        if source_note:
            if source is None:
                print(f"skip {path.name}:{key}: {source_note}")
                rebuilt.append(entry)
                cursor = end
                continue
            print(f"{path.name}:{key}: {source_note}")

        try:
            target, width, height, generated = prepare_image(
                source,
                max_width=args.max_width,
                quality=args.quality,
                force=args.force,
                dry_run=args.dry_run,
            )
        except ValueError as error:
            print(f"skip {path.name}:{key}: {error}")
            rebuilt.append(entry)
            cursor = end
            continue
        referenced_previews.add(target.resolve())

        updated = entry
        updated_any = False
        for field, value in (
            ("preview", preview_value_for(target, preview_dir)),
            ("preview_width", str(width)),
            ("preview_height", str(height)),
        ):
            updated, field_changed = set_field(updated, field, value)
            updated_any = updated_any or field_changed

        if generated:
            generated_images += 1
            action = "would generate" if args.dry_run else "generated"
            print(f"{action} {target.relative_to(ROOT)} ({width}x{height})")
        if updated_any:
            changed_entries += 1
            action = "would update" if args.dry_run else "updated"
            print(f"{action} {path.relative_to(ROOT)}:{key}")

        rebuilt.append(updated)
        cursor = end

    rebuilt.append(text[cursor:])
    new_text = "".join(rebuilt)
    if new_text != text and not args.dry_run:
        path.write_text(new_text, encoding="utf-8", newline="\n")
    return changed_entries, generated_images, referenced_previews


def clean_derived_previews(preview_dir: Path, referenced: set[Path], *, dry_run: bool) -> int:
    removed = 0
    for candidate in sorted(preview_dir.glob("*.webp")):
        if not width_derivative(candidate):
            continue
        if candidate.resolve() in referenced:
            continue
        removed += 1
        action = "would remove" if dry_run else "removed"
        print(f"{action} unused derived preview {candidate.relative_to(ROOT)}")
        if not dry_run:
            candidate.unlink()
    return removed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bib_files", nargs="*", type=Path, help="BibTeX files to update. Defaults to _bibliography/papers.bib.")
    parser.add_argument("--all", action="store_true", help="Update every .bib file in _bibliography.")
    parser.add_argument("--preview-dir", type=Path, default=DEFAULT_PREVIEW_DIR, help="Directory containing local preview images.")
    parser.add_argument("--max-width", type=int, default=DEFAULT_MAX_WIDTH, help="Maximum generated WebP width.")
    parser.add_argument("--quality", type=int, default=90, help="WebP quality, 1-100.")
    parser.add_argument("--force", action="store_true", help="Regenerate WebP files even when they already exist.")
    parser.add_argument("--dry-run", action="store_true", help="Report actions without writing files.")
    parser.add_argument(
        "--clean-derived",
        action="store_true",
        help="Remove unreferenced generated *-WIDTH.webp files from the preview directory.",
    )
    args = parser.parse_args()
    if args.max_width < 1:
        parser.error("--max-width must be a positive integer")
    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")
    return args


def main() -> int:
    args = parse_args()
    preview_dir = args.preview_dir
    if not preview_dir.is_absolute():
        preview_dir = ROOT / preview_dir

    if args.all:
        bib_files = sorted((ROOT / "_bibliography").glob("*.bib"))
    else:
        bib_files = args.bib_files or [DEFAULT_BIB]
        bib_files = [path if path.is_absolute() else ROOT / path for path in bib_files]

    total_entries = 0
    total_images = 0
    referenced_previews: set[Path] = set()
    for path in bib_files:
        if not path.exists():
            print(f"missing bib file: {path}", file=sys.stderr)
            return 1
        changed_entries, generated_images, entry_previews = process_bib(path, preview_dir, args)
        total_entries += changed_entries
        total_images += generated_images
        referenced_previews.update(entry_previews)

    removed_images = 0
    if args.clean_derived:
        removed_images = clean_derived_previews(preview_dir, referenced_previews, dry_run=args.dry_run)

    mode = "dry run: " if args.dry_run else ""
    print(f"{mode}{total_entries} entries updated, {total_images} images generated, {removed_images} images removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
