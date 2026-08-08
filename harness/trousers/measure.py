"""What shape the canon's trousers actually are, measured off both references.

Three questions, because the current build guesses at all three: where the
garment starts against the belt, how wide it is at the hip against the ankle,
and whether the two legs are separated by background or only by a drawn inseam.

**Measured off the silhouette, not off the garment's colour.** Picking the
trousers out by their own tone was tried first and fails on both sheets: the
canon shades the garment with folds and the chibi is a JPEG, so a tolerance wide
enough to hold the whole leg also holds the boots, and one tight enough to
exclude the boots breaks the leg into a dozen runs per row. The background, by
contrast, is flat near-white on both, so "not background" is exact. That answers
the gap question directly, which is the one that matters most: background
between the legs is a gap, and no background is an inseam drawn on solid cloth.

The tunic and belt are found by hue, which is safe because it only has to
separate green from brown from grey, not to trace anything.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def load(name: str) -> tuple[list[list[tuple[int, int, int]]], int, int]:
    # Flattened onto white rather than `convert("RGB")`. Our renders carry alpha
    # as of 2026-08-07, and discarding it leaves the background black, which
    # this file's whole method reads as figure: every measurement below would
    # come out wrong instead of failing. The references are opaque, so this
    # leaves them exactly as they were.
    im = Image.open(ROOT / name)
    if im.mode in ("RGBA", "LA") or "transparency" in im.info:
        sheet = Image.new("RGB", im.size, "white")
        im = im.convert("RGBA")
        sheet.paste(im, (0, 0), im)
        im = sheet
    else:
        im = im.convert("RGB")
    w, h = im.size
    px = im.load()
    return [[px[x, y] for x in range(w)] for y in range(h)], w, h


def runs(row: list[bool], min_len: int = 3) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    start = None
    for x, on in enumerate(row):
        if on and start is None:
            start = x
        elif not on and start is not None:
            if x - start >= min_len:
                out.append((start, x - 1))
            start = None
    if start is not None and len(row) - start >= min_len:
        out.append((start, len(row) - 1))
    return out


def report(name: str) -> None:
    a, w, h = load(name)

    def figure(y: int) -> list[bool]:
        """Not background, and not a hand.

        Skin has to come out because a chibi's arms hang at very nearly the
        hip's own width, so no x-window separates them from the body: with the
        hands left in, the widest run in a row below the belt is a hand and the
        "gap between the legs" is the daylight beside the hip.
        """
        out = []
        for x in range(w):
            r, g, b = a[y][x]
            skin = r > 195 and r > g + 12 and g > b and r - b > 28
            out.append(sum(255 - c for c in (r, g, b)) > 60 and not skin)
        return out

    def green(y: int) -> int:
        return sum(1 for r, g, b in a[y] if g > r + 10 and g > b + 10 and g < 180)

    def brown(y: int) -> int:
        # The belt's leather is only about 20 points redder than blue, and the
        # trousers are the other way round (bluer than red), so `r >= g` plus a
        # modest red-over-blue separates them without catching the garment.
        return sum(1 for r, g, b in a[y] if r >= g and r > b + 12 and 30 < r < 150)

    # The belt is the brown band nearest the tunic's own bottom. Half the peak
    # count rather than a fixed one, because the buckle and the highlight break
    # the band up and the two sheets are at different exposures.
    hem = max(y for y in range(h) if green(y) > 20)
    window = range(max(0, hem - 120), min(h, hem + 120))
    peak = max(brown(y) for y in window)
    belt_rows = [y for y in window if brown(y) > peak * 0.5]
    belt_top, belt_bot = min(belt_rows), max(belt_rows)
    belt_x = [x for y in belt_rows for x, (r, g, b) in enumerate(a[y]) if r >= g and r > b + 12]
    x_lo, x_hi = min(belt_x), max(belt_x)
    print(f"\n=== {name}")
    print(f"  tunic green ends at y={hem}, belt band y={belt_top}..{belt_bot} x={x_lo}..{x_hi}")
    print(f"  tunic hangs {hem - belt_bot:+d}px below the belt's bottom edge")

    # A run counts as leg only if it overlaps the middle 60% of the belt's own
    # width. Excluding skin is not enough on its own: the hand's black outline
    # survives it and still reads as a run. A hand hangs beside the hip, well
    # outside this window, and a leg always crosses it.
    cx = (x_lo + x_hi) / 2
    bw = x_hi - x_lo
    core_lo, core_hi = cx - bw * 0.30, cx + bw * 0.30
    lo, hi = 0, w

    def legs(y: int) -> list[tuple[int, int]]:
        return [r for r in runs(figure(y)) if r[1] >= core_lo and r[0] <= core_hi]

    bottom = max(y for y in range(h) if legs(y))
    print(f"  figure bottom y={bottom}, belt-to-floor {bottom - belt_bot}px")
    # The torso just above the belt, as the yardstick everything below is
    # reported against. A ratio against the body's own width needs no
    # calibration, which measuring in head radii would.
    torso = max(r[-1][1] - r[0][0] for r in [legs(y) for y in range(belt_top - 30, belt_top)] if r)
    print(f"  torso half-width just above the belt {torso / 2:.1f}px")

    drop = bottom - belt_bot
    split = None
    for frac in [i / 40 for i in range(41)]:
        y = min(round(belt_bot + drop * frac), h - 1)
        r = legs(y)
        if not r:
            continue
        gap = r[1][0] - r[0][1] - 1 if len(r) == 2 else 0
        if split is None and len(r) == 2:
            split = frac
        width = r[-1][1] - r[0][0]
        print(
            f"  {frac:4.2f}  y={y:4d}  outer {r[0][0]}..{r[-1][1]}"
            f"  half_w={width / 2:6.1f} ({width / torso:4.2f} torso)"
            f"  runs={len(r)}  gap={gap:4d}px  gap/width={gap / width:5.2f}"
        )
    print(f"  legs first separate at {split:.2f} of belt-to-floor")


# Our side reads the checked-in renders rather than a scratch pair, which is
# what it used to do: those lived in `out/` and went with the 2026-08-07
# cleanup. `ref-out/` is the shipped output and is regenerated by
# `./refresh-ref-out.sh`, so this now measures what actually ships.
for target in (
    "ref/satoshi-chibi.jpg",
    "ref/satoshi.png",
    "ref-out/satoshi.png",
    "ref-out/real/satoshi.png",
):
    report(target)
