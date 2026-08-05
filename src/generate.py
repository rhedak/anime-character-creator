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

# Expression knobs, mirrored from FaceStyle. See character.FaceStyle for what
# each one does and what the neutral value is.
FACE_ARGS: dict[str, type] = {
    "eye_size": float,
    "eye_width": float,
    "eye_openness": float,
    "eye_lower_lid": float,
    "eye_tilt": float,
    "eye_corner": float,
    "iris_size": float,
    "brow_tilt": float,
    "brow_weight": float,
    "mouth_curve": float,
    "mouth_width": float,
    "blush": float,
    "scar_side": int,
}


def _flag(name: str) -> str:
    return f"--{name.replace('_', '-')}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/character", help="output path prefix (no extension)")
    ap.add_argument("--preset", choices=sorted(PRESETS), help="start from a named character")
    for name in COLOR_ARGS:
        ap.add_argument(_flag(name), help="hex color, overrides the preset")
    for name, kind in FACE_ARGS.items():
        ap.add_argument(_flag(name), type=kind, help="expression knob, overrides the preset")
    ap.add_argument("--flat", action="store_true", help="disable cel-shading shadow shapes")
    args = ap.parse_args()

    base = PRESETS[args.preset] if args.preset else CharacterParams()
    colors = {name: getattr(args, name) for name in COLOR_ARGS if getattr(args, name) is not None}
    face = {name: getattr(args, name) for name in FACE_ARGS if getattr(args, name) is not None}
    params = replace(base, shaded=not args.flat, **colors)
    if face:
        params = replace(params, face=replace(params.face, **face))

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
