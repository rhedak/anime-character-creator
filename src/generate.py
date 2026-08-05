"""CLI: render a chibi character to SVG (and PNG, if cairosvg is available).

Usage:
    python src/generate.py --out out/demo --hair-color "#e8b84b" --eye-color "#4a9c6d"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from character import CharacterParams, render_character


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/character", help="output path prefix (no extension)")
    ap.add_argument("--skin-tone", default=CharacterParams.skin_tone)
    ap.add_argument("--hair-color", default=CharacterParams.hair_color)
    ap.add_argument("--eye-color", default=CharacterParams.eye_color)
    ap.add_argument("--outfit-color", default=CharacterParams.outfit_color)
    ap.add_argument("--boot-color", default=CharacterParams.boot_color)
    ap.add_argument("--flat", action="store_true", help="disable cel-shading shadow shapes")
    args = ap.parse_args()

    params = CharacterParams(
        skin_tone=args.skin_tone,
        hair_color=args.hair_color,
        eye_color=args.eye_color,
        outfit_color=args.outfit_color,
        boot_color=args.boot_color,
        shaded=not args.flat,
    )

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
