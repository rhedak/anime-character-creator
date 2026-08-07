"""CLI: render a character to SVG (and PNG, if cairosvg is available).

Usage, in the three spellings that all reach `main()`:

    ./render.sh --out out/satoko --preset satoko           # sets up cairo first
    anime-character-creator --out out/demo --hair-color "#e8b84b"
    python -m anime_character_creator --out out/demo --preset satoshi

`render.sh` is the one to prefer on macOS: PNG export needs an environment
variable set before the process starts. See the script for why.

Every flag here mirrors a field of `CharacterParams`, `Outfit` or `FaceStyle`,
generated from the tables below rather than written out one by one, so a new
knob on those dataclasses becomes a flag by being named here.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from .character import HAIRSTYLES, CharacterParams, render_character
from .presets import PRESETS
from .skeleton import BUILDS

COLOR_ARGS = ("skin_tone", "hair_color", "hair_tip_color", "eye_color")

# Garment knobs, mirrored from character.Outfit. A garment is worn when its
# color is set, so these add layers; they cannot take one away, since argparse
# has no way to say "None" on the command line. Drop the layer from the preset
# for that.
OUTFIT_ARGS: dict[str, type] = {
    "tunic_color": str,
    "boot_color": str,
    "undersleeve_color": str,
    "belt_color": str,
    "apron_color": str,
    "skirt_color": str,
    "underskirt_color": str,
    "trouser_color": str,
    "pouch_color": str,
    "skirt_length": float,
}

# --outfit-color named the one garment there used to be, and is documented, so
# it stays as an alias rather than breaking anyone's muscle memory.
ALIASES: dict[str, tuple[str, ...]] = {"tunic_color": ("--outfit-color",)}

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
    for name, kind in OUTFIT_ARGS.items():
        ap.add_argument(
            _flag(name), *ALIASES.get(name, ()), type=kind, help="garment, overrides the preset"
        )
    for name, kind in FACE_ARGS.items():
        ap.add_argument(_flag(name), type=kind, help="expression knob, overrides the preset")
    ap.add_argument("--build", choices=sorted(BUILDS), help="named proportions (default chibi)")
    ap.add_argument("--hairstyle", choices=sorted(HAIRSTYLES), help="which haircut")
    ap.add_argument("--hair-length", type=float, help="hair end, chin 0 to hip 1")
    ap.add_argument("--heads", type=float, help="head-heights tall, overrides --build")
    ap.add_argument("--frame", type=float, help="shoulder against hip, -1 to 1, taller builds only")
    ap.add_argument("--flat", action="store_true", help="disable cel-shading shadow shapes")
    ap.add_argument(
        "--background",
        help="paint a background, e.g. white; default is transparent, so the figure composites",
    )
    args = ap.parse_args()

    base = PRESETS[args.preset] if args.preset else CharacterParams()
    colors = {name: getattr(args, name) for name in COLOR_ARGS if getattr(args, name) is not None}
    outfit = {name: getattr(args, name) for name in OUTFIT_ARGS if getattr(args, name) is not None}
    face = {name: getattr(args, name) for name in FACE_ARGS if getattr(args, name) is not None}
    if args.build is not None:
        colors["heads"] = BUILDS[args.build]
    for extra in ("heads", "hair_length", "hairstyle", "frame"):
        if getattr(args, extra) is not None:
            colors[extra] = getattr(args, extra)
    params = replace(base, shaded=not args.flat, **colors)
    if outfit:
        params = replace(params, outfit=replace(params.outfit, **outfit))
    if face:
        params = replace(params, face=replace(params.face, **face))

    svg = render_character(params, background=args.background)

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
        print(
            f"cairosvg needs the system cairo library, which isn't available ({e}); SVG was still written"
        )


if __name__ == "__main__":
    main()
