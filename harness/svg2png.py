#!/usr/bin/env python3
"""Rasterise SVG files to PNG with cairosvg, the way the Python CLI did.

The drawing is TypeScript now (`ts/bin/render.ts` writes the SVG); PNG export stays
here because cairosvg is Python and the committed PNGs under `ref-out/` are what it
makes. This is the same call the Python CLI's `generate.py` made (in the tag `python-final`), `svg2png(bytestring=svg.encode(),
scale=2)`, so a PNG made from an SVG file is pixel-identical to the one the Python CLI
wrote beside it. Nothing is added to the PNG (the CLI's `--metadata` text chunk is not
written here; the refresh scripts never use it).

    harness/svg2png.py IN.svg OUT.png [IN2.svg OUT2.png ...] [--scale N]

Run it through the project's venv with the cairo environment variable that the old `render.sh`
sets (cairosvg finds libcairo through dlopen, which on macOS does not look in
Homebrew's prefix); `refresh-ref-out.sh` and `refresh-bases.sh` do.
Exit status 1 if cairo is missing or a file cannot be read.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    scale: float = 2
    files: list[str] = []
    it = iter(argv)
    for arg in it:
        if arg == "--scale":
            scale = float(next(it))
        elif arg.startswith("--scale="):
            scale = float(arg.split("=", 1)[1])
        else:
            files.append(arg)
    if not files or len(files) % 2:
        print("usage: svg2png.py IN.svg OUT.png [IN2.svg OUT2.png ...] [--scale N]", file=sys.stderr)
        return 2
    try:
        import cairosvg
    except ImportError:
        print("cairosvg is not installed; uv sync", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"cairosvg needs the system cairo library ({e}); brew install cairo", file=sys.stderr)
        return 1
    for src, dst in zip(files[::2], files[1::2], strict=True):
        svg = Path(src).read_bytes()
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(bytestring=svg, write_to=dst, scale=scale)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
