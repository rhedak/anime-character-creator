"""The D5 test set (todo steps 2 and 3): hair variants side by side, one command.

Nothing in `src/` changes: `_hair_mass` and `_hair_front` are stood in for
while rendering, the way `harness/trace_hair/preview.py` does, but from any
number of hair files at once, so a variant is a `hair.json`-schema file (the
`mass_parts`, `front_parts`, `front_edges`, `strands`) and nothing else. Variant
A (narrow, like `katherina_grok_real`) and variant B (the fuller flare) just
write their own file and are named here.

    ./harness/run.sh harness/hair_only/compare.py [VARIANT ...] [--only GROUP]

A `VARIANT` is `label` (the renderer's own hair, for `today`), or
`label=path.json` with options after commas: `lw=0.02` the strand line weight
in head radii (default the file's `line_width_r`), `min=0.3` drop strands
shorter than that many head radii, `nolines` draw none. With no variant given:
`today` and `current=out/hair_only/hair.json`. Rows are variants, columns cases.

Groups, one sheet each (`out/hair_only/compare_<group>.png`):

- `katherina`: the two references (`katherina_grok_real` and the hair-only one
  at its registration), then Katherina at 1.3 with her hat, without it, and
  in blonde. Heads and torso, 2x.
- `others`: Linnea (pink), Satoko (pale tips), Chiyo, Reika (near black), each
  at its own height, under the same traced hair. This is the test the trace
  fails by construction: a fixed cut for one body.
- `full`: whole figures, Katherina with and without the hat and Satoko, 1x.
- `small`: Katherina at the insert size, head radius 21 px, 1x and 2x, shown 2x.
- `heights`: Katherina without her hat at heights 0.8, 1.0, 1.15 and 1.3. The
  hair files are fitted at 1.3 (the trace's belt squeeze), so this is where
  that shows.
"""

import io
import json
import sys
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.colorutil import shade
from anime_character_creator.presets import PRESETS

OUT = "out/hair_only"
BASE = f"{OUT}/hair.json"
REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
REF_HAIR = "ref-local/katherina_hair/hair_only.png"
TALL = 1.3
PAD = (2.4, 1.5, 2.4, 4.8)
GROUPS = ("katherina", "others", "full", "small", "heights")
ORIG = (c._hair_mass, c._hair_front)


def load(path):
    return json.load(open(path))


def _length(chain) -> float:
    (x0, y0), segs = chain
    total, p = 0.0, (x0, y0)
    for _, e in segs:
        total += ((e[0] - p[0]) ** 2 + (e[1] - p[1]) ** 2) ** 0.5
        p = e
    return total


def _pieces_d(sk, hair, key):
    """One path for a shape: the parts and holes the trace kept, for an
    even-odd fill, or its single outline. The extra outlines are what a front
    piece strokes besides its `front_edges`."""
    ps = hair.get(f"{key}_parts") or []
    if not ps:
        return c._curve(sk.head_cx, sk.head_cy, sk.head_r, *hair[key]), []
    ds, extra = [], []
    biggest = max(range(len(ps)), key=lambda i: len(ps[i][0][1]))
    for i, (outer, holes) in enumerate(ps):
        ds.append(c._curve(sk.head_cx, sk.head_cy, sk.head_r, *outer))
        if i != biggest:
            extra.append(outer)
        for h in holes:
            ds.append(c._curve(sk.head_cx, sk.head_cy, sk.head_r, *h))
            extra.append(h)
    return " ".join(ds), extra


def _stroke(sk, chain, w, clip):
    d = c._curve(sk.head_cx, sk.head_cy, sk.head_r, *chain, close=False)
    return (
        f'<path d="{d}" fill="none" stroke="{c.OUTLINE}" stroke-width="{w:.2f}" '
        f'stroke-linecap="round" stroke-linejoin="round" clip-path="url(#{clip})" />'
    )


def _near(p, polys, tol):
    """Whether `p` lies within `tol` of any polyline in `polys`."""
    for poly in polys:
        for a, b in zip(poly[:-1], poly[1:]):
            ax, ay, bx, by = *a, *b
            ab2 = (bx - ax) ** 2 + (by - ay) ** 2 or 1e-9
            t = min(max(((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / ab2, 0.0), 1.0)
            if (p[0] - ax - t * (bx - ax)) ** 2 + (p[1] - ay - t * (by - ay)) ** 2 <= tol * tol:
                return True
    return False


def _runs(chain, thin, tol=0.05):
    """A closed outline's segments grouped into runs that lie along the
    `thin` polylines (the lock's outer edge, which the reference draws fine)
    or not: a list of (chain, is_thin)."""
    if not thin:
        return [(chain, False)]
    (x0, y0), segs = chain
    runs, cur, p = [], None, (x0, y0)
    for ctrl, end in segs:
        is_thin = _near(p, thin, tol) and _near(end, thin, tol)
        if cur is None or cur[2] != is_thin:
            cur = [p, [], is_thin]
            runs.append(cur)
        cur[1].append((ctrl, end))
        p = end
    return [((start, ss), t) for start, ss, t in runs]


def stand_in(hair, lw=None, min_len=0.0, lines=True):
    """`_hair_mass` and `_hair_front` drawing `hair`, where they draw."""
    lw = hair.get("line_width_r", 0.0114) if lw is None else lw
    strands = [s for s in hair["strands"] if _length(s["chain"]) >= min_len] if lines else []
    uid = f"hc{id(hair) % 100000}"

    def mass(sk, p):
        d, _ = _pieces_d(sk, hair, "mass")
        parts = [f'<defs><clipPath id="{uid}m"><path d="{d}" clip-rule="evenodd" /></clipPath></defs>']
        parts += [x.replace(f'd="{d}"', f'd="{d}" fill-rule="evenodd"') for x in c._two_tone_hair(d, p)]
        # A darker patch of the back hair (the owner's cyan), on the mass.
        for ch in hair.get("dark_parts", []):
            dd = c._curve(sk.head_cx, sk.head_cy, sk.head_r, *ch)
            tone = shade(p.hair_color, hair.get("dark_factor", 0.65))
            parts.append(f'<path d="{dd}" fill="{tone}" clip-path="url(#{uid}m)" />')
        for s in strands:
            if not s["front"]:
                parts.append(_stroke(sk, s["chain"], lw * sk.head_r, f"{uid}m"))
        parts.append(
            f'<path d="{d}" fill="none" stroke="{c.OUTLINE}" stroke-width="{c._outline_w(c._stroke_w(sk)):.2f}" '
            f'stroke-linejoin="round" />'
        )
        return "".join(parts)

    def front(sk, p):
        sw = c._stroke_w(sk)
        d, extra = _pieces_d(sk, hair, "front")
        parts = [f'<defs><clipPath id="{uid}f"><path d="{d}" clip-rule="evenodd" /></clipPath></defs>']
        parts += [x.replace(f'd="{d}"', f'd="{d}" fill-rule="evenodd"') for x in c._two_tone_hair(d, p)]
        for s in strands:
            if s["front"]:
                parts.append(_stroke(sk, s["chain"], lw * sk.head_r, f"{uid}f"))
        for e in [*hair["front_edges"], *extra]:
            for run, is_thin in _runs(e, hair.get("thin_edges", [])):
                d_e = c._curve(sk.head_cx, sk.head_cy, sk.head_r, *run, close=False)
                w = c._interior_w(sw, 0.55) if is_thin else c._outline_w(sw)
                parts.append(
                    f'<path d="{d_e}" fill="none" stroke="{c.OUTLINE}" stroke-width="{w:.2f}" '
                    f'stroke-linecap="round" stroke-linejoin="round" />'
                )
        return "".join(parts)

    return mass, front


def parse(spec):
    """`label`, or `label=path[,lw=..][,min=..][,nolines]` to (label, functions)."""
    label, _, rest = spec.partition("=")
    if not rest:
        if label != "today":
            sys.exit(f"variant {label!r} needs a path: {label}=path.json")
        return label, ORIG
    path, *opts = rest.split(",")
    kw = {}
    for o in opts:
        if o == "nolines":
            kw["lines"] = False
        elif o.startswith("lw="):
            kw["lw"] = float(o[3:])
        elif o.startswith("min="):
            kw["min_len"] = float(o[4:])
        else:
            sys.exit(f"unknown option {o!r}")
    return label, stand_in(load(path), **kw)


def cases(group):
    k = replace(PRESETS["katherina"], height=TALL)
    bare = replace(k, outfit=replace(k.outfit, hat_color=None))
    blonde = replace(bare, hair_color="#e0c060")
    if group == "katherina":
        return [("katherina h1.3", k), ("katherina h1.3, no hat", bare), ("katherina blonde", blonde)]
    if group == "others":
        return [(n, PRESETS[n]) for n in ("linnea", "satoko", "chiyo", "reika")]
    if group == "heights":
        return [(f"katherina h{h}, no hat", replace(bare, height=h)) for h in (0.8, 1.0, 1.15, 1.3)]
    if group == "full":
        return [("katherina h1.3", k), ("katherina h1.3, no hat", bare), ("satoko", PRESETS["satoko"])]
    return [("katherina h1.3", k)]


def render(p, scale):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def crop(im, sk, k, pad):
    r, cx, cy = sk.head_r * k, sk.head_cx * k, sk.head_cy * k
    return im.crop((int(cx - pad[0] * r), int(cy - pad[1] * r), int(cx + pad[2] * r), int(cy + pad[3] * r)))


def label(t, text):
    ImageDraw.Draw(t).text((3, 3), text, fill=(200, 0, 0))
    return t


def reference_tiles(size):
    """Both references cut to the same head-radius window as a head tile, in
    the trace's frame (D0's face-width calibration; the hair-only one placed by
    its registration and unsqueezed), scaled to `size`."""
    base = load(BASE)
    (ox, oy), s = base["calibration"]["origin"], base["calibration"]["px_per_r"]
    box = (ox - PAD[0] * s, oy - PAD[1] * s, ox + PAD[2] * s, oy + PAD[3] * s)
    old = Image.open(REF).convert("RGB").crop(tuple(int(v) for v in box)).resize(size, Image.LANCZOS)
    sc, (dx, dy) = base["new_ref"]["scale"], base["new_ref"]["offset"]
    ref = Image.open(REF_HAIR).convert("RGBA")
    bg = Image.new("RGBA", ref.size, (255, 255, 255, 255))
    bg.alpha_composite(ref)
    nb = tuple(int((v - o) / sc) for v, o in zip(box, (dx, dy, dx, dy)))
    new = bg.convert("RGB").crop(nb).resize(size, Image.LANCZOS)
    return label(old, "reference: katherina_grok_real"), label(new, "reference: hair-only, unsqueezed")


def grid(rows, path):
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (max(len(r) for r in rows) * (tw + 4), len(rows) * (th + 4)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 4), j * (th + 4)))
    sheet.save(path)
    print(path, sheet.size)


def sheet(group, variants):
    rows = []
    for name, fns in variants:
        c._hair_mass, c._hair_front = fns
        row = []
        for cname, p in cases(group):
            tag = f"{name} / {cname}"
            if group == "small":
                sk = c.skeleton_for(p)
                tiles = []
                for density in (1, 2):
                    k = 21.0 * density / sk.head_r
                    im, _ = render(p, k * 4)
                    tiles.append(im.resize((im.width // 4, im.height // 4), Image.LANCZOS))
                both = Image.new("RGB", (tiles[0].width + tiles[1].width + 4, tiles[1].height), (255, 255, 255))
                both.paste(tiles[0], (0, 0))
                both.paste(tiles[1], (tiles[0].width + 4, 0))
                row.append(label(both.resize((both.width * 2, both.height * 2), Image.NEAREST), name))
            elif group == "full":
                im, _ = render(p, 1)
                row.append(label(im, tag))
            else:
                im, sk = render(p, 2)
                row.append(label(crop(im, sk, 2, PAD), tag))
        rows.append(row)
    if group == "katherina":
        size = rows[0][0].size
        old, new = reference_tiles(size)
        for row in rows:
            row[:0] = [old.copy(), new.copy()]
    grid(rows, f"{OUT}/compare_{group}.png")


def main() -> None:
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only")
        only = args[i + 1]
        args = args[:i] + args[i + 2 :]
        if only not in GROUPS:
            sys.exit(f"--only takes one of {', '.join(GROUPS)}")
    specs = args or ["today", f"current={BASE}"]
    variants = [parse(s) for s in specs]
    try:
        for group in [only] if only else GROUPS:
            sheet(group, variants)
    finally:
        c._hair_mass, c._hair_front = ORIG


if __name__ == "__main__":
    main()
