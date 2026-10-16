"""Gate 1 pairs (`docs/soft-hair-plan.md`): the package's soft finish with the clumps against the same
without them, on every authored preset, left and right drawn per row, only a row number shown.

    ./harness/run.sh harness/soft_hair/gate1.py --seed 51

Writes `out/soft/gate1-<seed>/pairs-app.png` (the app's close-up size), `pairs-zoom.png` (the head
enlarged) and `key.json` (not to be opened before choosing). The last-drawn row is a control: the same
picture on both sides.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, "harness/soft_hair")
sys.path.insert(0, "src")
import cast  # noqa: E402
from anime_character_creator import HAIRSTYLES, PRESETS  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--seed", type=int, default=51)
    ap.add_argument("--out", default="out/soft")
    args = ap.parse_args()
    authored = [n for n in sorted(PRESETS) if HAIRSTYLES[PRESETS[n].hairstyle].locks is not None]
    rng = random.Random(f"gate1-{args.seed}")
    rows = [(n, "pair") for n in authored] + [(authored[0], "control")]
    rng.shuffle(rows)
    sides = [rng.random() < 0.5 for _ in rows]  # True: the clumps on the left
    out = Path(args.out) / f"gate1-{args.seed}"
    out.mkdir(parents=True, exist_ok=True)
    key = {}
    for view, suffix in (("app", "app"), ("face", "zoom")):
        w, h = cast.VIEWS[view][1]
        if view == "face":
            w, h = w // 2, h // 2
        img = Image.new("RGB", (2 * w + 6, len(rows) * (h + 6) - 6), "white")
        for i, ((name, kind), clumps_left) in enumerate(zip(rows, sides, strict=True)):
            y = i * (h + 6)
            if kind == "control":
                left = right = cast.draw(name, view, False)
                key[str(i + 1)] = {
                    "preset": name,
                    "left": "control (no clumps)",
                    "right": "control (no clumps)",
                }
            else:
                a, b = cast.draw(name, view, True), cast.draw(name, view, False)
                left, right = (a, b) if clumps_left else (b, a)
                key[str(i + 1)] = {
                    "preset": name,
                    "left": "clumps" if clumps_left else "no clumps",
                    "right": "no clumps" if clumps_left else "clumps",
                }
            for x, im in ((0, left), (w + 6, right)):
                img.paste(im.resize((w, h), Image.LANCZOS) if im.size != (w, h) else im, (x, y))
            ImageDraw.Draw(img).text((10, y + 8), str(i + 1), fill="white")
        img.save(out / f"pairs-{suffix}.png")
    (out / "key.json").write_text(json.dumps(key, indent=1))
    print("wrote", out, "rows:", len(rows))


if __name__ == "__main__":
    main()
