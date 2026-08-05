"""CLI: render a chibi character to SVG (and PNG, if cairosvg is available).

Usage:
    python src/generate.py --out out/demo --hair-color "#e8b84b" --eye-color "#4a9c6d"
    python src/generate.py --out out/satoko --preset satoko
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from character import CharacterParams, render_character
from presets import PRESETS

COLOR_ARGS = ("skin_tone", "hair_color", "hair_tip_color", "eye_color", "outfit_color", "boot_color")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/character", help="output path prefix (no extension)")
    ap.add_argument("--preset", choices=sorted(PRESETS), help="start from a named character")
    for name in COLOR_ARGS:
        ap.add_argument(f"--{name.replace('_', '-')}", help="hex color, overrides the preset")
    ap.add_argument("--flat", action="store_true", help="disable cel-shading shadow shapes")
    args = ap.parse_args()

    base = PRESETS[args.preset] if args.preset else CharacterParams()
    overrides = {name: getattr(args, name) for name in COLOR_ARGS if getattr(args, name) is not None}
    params = replace(base, shaded=not args.flat, **overrides)

    svg = render_character(params)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path = out_path.with_suffix(".svg")
    svg_path.write_text(svg)
    print(f"wrote {svg_path}")

    try:
        import cairosvg

        png_path = out_path.with_suffix(".png")
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(png_path), scale=2)
        print(f"wrote {png_path}")
    except ImportError:
        print("cairosvg not installed; skipping PNG export (SVG is still valid, open it directly)")
    except OSError as e:
        print(f"cairosvg needs the system cairo library, which isn't available ({e}); SVG was still written")


if __name__ == "__main__":
    main()
