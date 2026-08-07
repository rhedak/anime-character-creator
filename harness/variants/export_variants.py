"""Write every variant tried this round to out/variants/, full size, plus the
side-by-side comparison sheets.

Each variant is a standalone set of shape functions, so this does not depend on
what the source currently happens to hold: the superseded states are reproduced
here on purpose, which is the point of keeping them. Everything lands under
out/variants/, which .gitignore already covers.
"""

import io
import os
import sys
from dataclasses import replace

ROOT = "/Users/hanssen.henrik/git/self-study/anime-character-creator"
SP = "/private/tmp/claude-502/-Users-hanssen-henrik-git-self-study/0c0afc98-b92a-410a-91c9-416981d904b8/scratchpad"
sys.path.insert(0, ROOT + "/src")
sys.path.insert(0, SP)
os.chdir(ROOT)

import cairosvg
from PIL import Image, ImageDraw

import character as C
import hairlab as HL
import leglab as LL
from colorutil import shade
from presets import SATOKO, SATOSHI

OUT = ROOT + "/out/variants"
SHIPPED_HAIR = C.HAIRSTYLES["short_layered"]
SHIPPED_LEGS = C._legs_and_boots
SHIPPED_BOOT = C._boot


def write(sub, name, p, w=800, h=1000):
    d = f"{OUT}/{sub}"
    os.makedirs(d, exist_ok=True)
    svg = C.render_character(p)
    open(f"{d}/{name}.svg", "w").write(svg)
    raw = cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h)
    open(f"{d}/{name}.png", "wb").write(raw)
    return Image.open(io.BytesIO(raw)).convert("RGB")


def reset():
    C.HAIRSTYLES["short_layered"] = SHIPPED_HAIR
    C._legs_and_boots = SHIPPED_LEGS
    C._boot = SHIPPED_BOOT


# ------------------------------------------------------------------ old boot

def boot_pre(sk, p, cx, w_ankle, w_knee):
    """The boot as it was before this round: foot measured off the ankle at 3.4x
    and shaft off the knee, which is why widening the shin ballooned the shoe."""
    color = p.outfit.boot_color
    boot_w = w_ankle * 3.4
    foot_h = sk.foot_y - sk.ankle_y
    top_y = sk.ankle_y - (sk.ankle_y - sk.knee_y) * 0.32
    shaft_w = w_knee * 1.16
    instep_y = sk.ankle_y + foot_h * 0.30
    r = boot_w * 0.22
    d = (
        f"M {cx - shaft_w:.1f} {top_y:.1f} L {cx - shaft_w:.1f} {sk.ankle_y:.1f} "
        f"Q {cx - boot_w / 2:.1f} {instep_y:.1f} {cx - boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f"Q {cx - boot_w / 2:.1f} {sk.foot_y:.1f} {cx - boot_w / 2 + r:.1f} {sk.foot_y:.1f} "
        f"L {cx + boot_w / 2 - r:.1f} {sk.foot_y:.1f} "
        f"Q {cx + boot_w / 2:.1f} {sk.foot_y:.1f} {cx + boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f"Q {cx + boot_w / 2:.1f} {instep_y:.1f} {cx + shaft_w:.1f} {sk.ankle_y:.1f} "
        f"L {cx + shaft_w:.1f} {top_y:.1f} Z"
    )
    parts = [f'<path d="{d}" fill="{color}" stroke="{C.OUTLINE}" stroke-width="{C.STROKE_W}" />']
    if not p.shaded:
        return "".join(parts)
    sole_h = foot_h * 0.24
    parts.append(
        f'<path d="M {cx - boot_w / 2:.1f} {sk.foot_y - sole_h:.1f} L {cx + boot_w / 2:.1f} {sk.foot_y - sole_h:.1f} '
        f"L {cx + boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f"Q {cx + boot_w / 2:.1f} {sk.foot_y:.1f} {cx + boot_w / 2 - r:.1f} {sk.foot_y:.1f} "
        f"L {cx - boot_w / 2 + r:.1f} {sk.foot_y:.1f} "
        f"Q {cx - boot_w / 2:.1f} {sk.foot_y:.1f} {cx - boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f'Z" fill="{shade(color, 0.7)}" />'
    )
    parts.append(
        f'<line x1="{cx - shaft_w:.1f}" y1="{top_y + (sk.ankle_y - top_y) * 0.3:.1f}" '
        f'x2="{cx + shaft_w:.1f}" y2="{top_y + (sk.ankle_y - top_y) * 0.3:.1f}" '
        f'stroke="{shade(color, 0.7)}" stroke-width="{max(1.5, C.STROKE_W * 0.6):.1f}" />'
    )
    return "".join(parts)


def _boot_with(sk, p, cx, w_ankle, foot_mult, shaft_mult):
    lo, hi = foot_mult
    color = p.outfit.boot_color
    boot_w = sk.leg_half_w * (lo - (lo - hi) * sk.build)
    foot_h = sk.foot_y - sk.ankle_y
    top_y = sk.ankle_y - (sk.ankle_y - sk.knee_y) * 0.32
    shaft_w = w_ankle * shaft_mult
    instep_y = sk.ankle_y + foot_h * 0.30
    r = boot_w * 0.22
    d = (
        f"M {cx - shaft_w:.1f} {top_y:.1f} L {cx - shaft_w:.1f} {sk.ankle_y:.1f} "
        f"Q {cx - boot_w / 2:.1f} {instep_y:.1f} {cx - boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f"Q {cx - boot_w / 2:.1f} {sk.foot_y:.1f} {cx - boot_w / 2 + r:.1f} {sk.foot_y:.1f} "
        f"L {cx + boot_w / 2 - r:.1f} {sk.foot_y:.1f} "
        f"Q {cx + boot_w / 2:.1f} {sk.foot_y:.1f} {cx + boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f"Q {cx + boot_w / 2:.1f} {instep_y:.1f} {cx + shaft_w:.1f} {sk.ankle_y:.1f} "
        f"L {cx + shaft_w:.1f} {top_y:.1f} Z"
    )
    parts = [f'<path d="{d}" fill="{color}" stroke="{C.OUTLINE}" stroke-width="{C.STROKE_W}" />']
    if p.shaded:
        sole_h = foot_h * 0.24
        parts.append(
            f'<path d="M {cx - boot_w / 2:.1f} {sk.foot_y - sole_h:.1f} L {cx + boot_w / 2:.1f} {sk.foot_y - sole_h:.1f} '
            f"L {cx + boot_w / 2:.1f} {sk.foot_y - r:.1f} "
            f"Q {cx + boot_w / 2:.1f} {sk.foot_y:.1f} {cx + boot_w / 2 - r:.1f} {sk.foot_y:.1f} "
            f"L {cx - boot_w / 2 + r:.1f} {sk.foot_y:.1f} "
            f"Q {cx - boot_w / 2:.1f} {sk.foot_y:.1f} {cx - boot_w / 2:.1f} {sk.foot_y - r:.1f} "
            f'Z" fill="{shade(color, 0.7)}" />'
        )
        parts.append(
            f'<line x1="{cx - shaft_w:.1f}" y1="{top_y + (sk.ankle_y - top_y) * 0.3:.1f}" '
            f'x2="{cx + shaft_w:.1f}" y2="{top_y + (sk.ankle_y - top_y) * 0.3:.1f}" '
            f'stroke="{shade(color, 0.7)}" stroke-width="{max(1.5, C.STROKE_W * 0.6):.1f}" />'
        )
    return "".join(parts)


# ------------------------------------------------------------------- sheets

def tile(pairs, out, cols=None):
    cols = cols or len(pairs)
    rows = (len(pairs) + cols - 1) // cols
    w = max(i.width for _, i in pairs)
    h = max(i.height for _, i in pairs)
    canvas = Image.new("RGB", ((w + 8) * cols, (h + 20) * rows), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    for k, (lab, im) in enumerate(pairs):
        cx, cy = (k % cols) * (w + 8), (k // cols) * (h + 20)
        canvas.paste(im, (cx, cy + 20))
        d.text((cx + 3, cy + 5), lab, fill=(0, 0, 0))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.save(out)


def small(im, w=200):
    return im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)


def head(im, w=260):
    c = im.crop((100, 0, 700, 470))
    return c.resize((w, int(w * c.height / c.width)), Image.LANCZOS)


def lower(im, w=210):
    c = im.crop((150, 440, 650, 1000))
    return c.resize((w, int(w * c.height / c.width)), Image.LANCZOS)


# =========================================================== hair variants

HAIR_STEPS = [
    ("01_pot_as_committed", HL.style(HL.mass_smooth, HL.edge_smooth, HL.line_smooth_low, HL.CROWN_SMOOTH), 0.45),
    ("02_jagged_mass", HL.style(HL.mass_jagged, HL.edge_jagged, HL.line_smooth_low_wide, HL.CROWN_JAGGED), 0.45),
    ("03_wedge_fringe", HL.style(HL.mass_jagged, HL.edge_jagged, HL.line_wedges, HL.CROWN_JAGGED), 0.45),
    ("04_wedges_plus_strands", HL.style(HL.mass_jagged, HL.edge_jagged, HL.line_wedges, HL.CROWN_JAGGED,
                                       strands=HL.strands_swept), 0.45),
    ("05_full_volume", HL.style(HL.mass_full, HL.edge_full, HL.line_wedges_soft, HL.CROWN_FULL,
                               fade=0.60, strands=HL.strands_layered), 0.45),
    ("06_full_no_strands", HL.style(HL.mass_full, HL.edge_full, HL.line_wedges_soft, HL.CROWN_FULL,
                                    fade=0.60), 0.45),
    ("07_crown_tufts_rejected", HL.style(HL.mass_tufted, HL.edge_full, HL.line_wedges_soft, HL.CROWN_TUFTED,
                                        fade=0.60, strands=HL.strands_layered), 0.45),
    ("08_shipped", None, 0.65),
]

HAIR_LENGTHS = [0.45, 0.65, 0.85, 1.00]
HAIR_FADES = [0.30, 0.42, 0.55, 0.70]
HAIR_WEIGHTS = [0.0, 0.40, 0.55, 0.85]


def do_hair():
    sheets = []
    for name, st, length in HAIR_STEPS:
        reset()
        if st is not None:
            C.HAIRSTYLES["short_layered"] = st
        p = replace(SATOSHI, hair_length=length)
        im = write("hair", name, p)
        write("hair", name + "_real", replace(p, heads=6.0))
        sheets.append((name.split("_", 1)[1], head(im)))
    reset()
    tile(sheets + [("ref", small(Image.open("ref/satoshi.png").convert("RGB").crop((330, 30, 560, 260)), 260))],
         f"{OUT}/compare/hair_steps.png", cols=5)

    # lock length, on the winning shape
    st = HL.style(HL.mass_full, HL.edge_full, HL.line_wedges_soft, HL.CROWN_FULL,
                  fade=0.42, strands=HL.strands_layered)
    C.HAIRSTYLES["short_layered"] = st
    pairs = []
    for L in HAIR_LENGTHS:
        im = write("hair_length", f"len_{L:.2f}", replace(SATOSHI, hair_length=L))
        pairs.append((f"len {L}", head(im)))
    tile(pairs, f"{OUT}/compare/hair_length.png")

    pairs = []
    for f in HAIR_FADES:
        C.HAIRSTYLES["short_layered"] = HL.style(
            HL.mass_full, HL.edge_full, HL.line_wedges_soft, HL.CROWN_FULL,
            fade=f, strands=HL.strands_layered)
        im = write("hair_fade", f"fade_{f:.2f}", replace(SATOSHI, hair_length=0.65))
        pairs.append((f"fade {f}", head(im)))
    tile(pairs, f"{OUT}/compare/hair_fade.png")

    # strand weight: patch the emitted stroke width, which is the only way to vary
    # it without a knob on Hairstyle, and Hairstyle does not need one
    reset()
    pairs = []
    for m in HAIR_WEIGHTS:
        svg = C.render_character(replace(SATOSHI))
        svg = svg.replace('stroke-width="1.7"', f'stroke-width="{max(3 * m, 0.001):.3f}"')
        d = f"{OUT}/hair_strand_weight"
        os.makedirs(d, exist_ok=True)
        open(f"{d}/weight_{m:.2f}.svg", "w").write(svg)
        raw = cairosvg.svg2png(bytestring=svg.encode(), output_width=800, output_height=1000)
        open(f"{d}/weight_{m:.2f}.png", "wb").write(raw)
        pairs.append((f"w {m}", head(Image.open(io.BytesIO(raw)).convert("RGB"))))
    tile(pairs, f"{OUT}/compare/hair_strand_weight.png")


# ============================================================ leg variants

LEG_STEPS = [
    ("01_cone_as_committed", LL.prof_current, boot_pre),
    ("02_straight_tube", LL.prof_straight, LL.boot_from_leg),
    ("03_measured", LL.prof_measured, LL.boot_from_leg),
    ("04_measured_slim", LL.prof_measured_slim, LL.boot_from_leg),
    ("05_shipped", None, None),
]


def do_legs():
    for preset, tag in ((SATOSHI, "satoshi"), (SATOKO, "satoko")):
        for heads, bt in ((None, "chibi"), (6.0, "real")):
            pairs = []
            for name, prof, boot in LEG_STEPS:
                reset()
                if prof is not None:
                    C._boot = boot
                    C._legs_and_boots = LL.make_legs(prof, boot)
                kw = {} if heads is None else {"heads": heads}
                im = write("legs", f"{tag}_{bt}_{name}", replace(preset, **kw))
                pairs.append((name.split("_", 1)[1], lower(im)))
            reset()
            extra = []
            if tag == "satoshi" and bt == "real":
                r = Image.open("ref/satoshi.png").convert("RGB").crop((250, 490, 650, 1170))
                extra = [("ref", small(r, 210))]
            tile(pairs + extra, f"{OUT}/compare/legs_{tag}_{bt}.png")

    # the boot on its own: three foot-vs-shaft ratios at the tall build
    pairs = []
    for name, boot in (
        ("01_ankle_x3.4_shaft_knee", boot_pre),
        ("02_foot_1.90_shaft_1.18", lambda *a: _boot_with(*a[:4], foot_mult=(2.90, 1.90), shaft_mult=1.18)),
        ("03_shipped_foot_2.00_shaft_1.10", None),
    ):
        reset()
        if boot is not None:
            C._boot = boot
        im = write("boots", name, replace(SATOSHI, heads=6.0))
        c = im.crop((280, 820, 520, 1000))
        pairs.append((name.split("_", 1)[1], c.resize((200, int(200 * c.height / c.width)), Image.LANCZOS)))
    reset()
    r = Image.open("ref/satoshi.png").convert("RGB").crop((270, 980, 640, 1180))
    tile(pairs + [("ref", small(r, 200))], f"{OUT}/compare/boots.png")


# ================================================= headroom, targets, palette

def do_rest():
    reset()
    # the shipped four, and a mid-build
    pairs = []
    for tag, preset in (("satoko", SATOKO), ("satoshi", SATOSHI)):
        for heads, bt in ((None, "chibi"), (4.0, "mid"), (6.0, "real")):
            kw = {} if heads is None else {"heads": heads}
            im = write("targets", f"{tag}_{bt}", replace(preset, **kw))
            pairs.append((f"{tag} {bt}", small(im)))
    tile(pairs, f"{OUT}/compare/targets.png", cols=3)

    # a palette nowhere near the defaults, which is what exercises shade()
    loud = replace(
        SATOKO, skin_tone="#5b3a2e", hair_color="#2a3f8f", hair_tip_color="#c74bd8", eye_color="#e8452b",
        outfit=replace(SATOKO.outfit, tunic_color="#8f1d4a", skirt_color="#1d8f7a",
                       underskirt_color="#e0d24a", belt_color="#0d0d12", apron_color="#c8c8d4",
                       undersleeve_color="#2e2e2e", boot_color="#d94f00"))
    pairs = []
    for name, p in (
        ("loud_chibi", loud),
        ("loud_real", replace(loud, heads=6.0)),
        ("loud_short_cut", replace(loud, hairstyle="short_layered", hair_length=0.65, heads=6.0)),
        ("satoko_short_cut", replace(SATOKO, hairstyle="short_layered", hair_length=0.65)),
        ("satoshi_long_cut", replace(SATOSHI, hairstyle="long_blunt", hair_length=0.5)),
        ("satoshi_flat", replace(SATOSHI, shaded=False)),
    ):
        pairs.append((name, small(write("cross_checks", name, p))))
    tile(pairs, f"{OUT}/compare/cross_checks.png", cols=3)

    # headroom: the committed chibi sliced flat against the canvas top, next to
    # the same crown with hair_margin in place
    before = Image.open(f"{SP}/base/satoko.png").convert("RGB").crop((170, 0, 630, 140))
    after = Image.open(f"{OUT}/targets/satoko_chibi.png").convert("RGB").crop((170, 0, 630, 140))
    tile([("clipped (committed)", small(before, 300)), ("hair_margin (shipped)", small(after, 300))],
         f"{OUT}/compare/headroom.png")


INDEX = """# Variants

Everything tried while reworking Satoshi's hair and legs, full size, both as
`.svg` and `.png`. Regenerate with `export_variants.py`, which sits next to this
file. That whole tree is covered by `.gitignore`, the script included, so if
`out/` is ever cleaned the script goes with it: copy it somewhere first if the
superseded shapes are worth keeping.

Read the `compare/` sheets first. They are the same renders cropped and tiled,
and they are the point: each one settles a question by putting the candidates
next to `ref/satoshi.png` rather than by argument.

## One caveat about the superseded variants

Every variant here is rendered by the *current* skeleton, which has the
`hair_margin` headroom fix in it. So the ones named `as_committed` reproduce the
committed **shape** but not the committed **output**: the committed chibis had
the top of their hair sliced flat against the canvas edge, and these do not.
`committed_baseline/` holds the actual four committed renders for that
comparison, and `compare/headroom.png` shows the clipping directly.

## Folders

| Folder | What is in it |
| --- | --- |
| `committed_baseline/` | The four targets exactly as committed at `92736d0`, before any of this |
| `targets/` | The shipped four, plus each character at 4 heads |
| `compare/` | Side-by-side sheets, one per question settled |
| `hair/` | The short cut in eight states, worst to shipped, each at both builds |
| `hair_length/` | Lock length 0.45 / 0.65 / 0.85 / 1.00 on the winning shape |
| `hair_fade/` | Where the two tones meet, four depths |
| `hair_strand_weight/` | Strand line weight, 0 through 0.85 of the outline |
| `legs/` | Five leg profiles, both characters, both builds |
| `boots/` | Three foot-against-shaft ratios at the tall build |
| `cross_checks/` | A palette far from the defaults, each cut on the other character, flat mode |

## What shipped, and what each variant was for

**Hair**, in `hair/`:

1. `01_pot_as_committed` shape the complaint was about: the mass follows the
   skull, so hair and head are nearly the same outline, and there is no interior
   line anywhere.
2. `02_jagged_mass` pointed lock ends, still hugging the skull. Barely moves it.
3. `03_wedge_fringe` fringe in wedge locks. Big change, but the notches between
   them rise the whole way and it comes out as a row of teeth.
4. `04_wedges_plus_strands` first version that reads as hair.
5. `05_full_volume` the mass standing off the skull, softened notches.
6. `06_full_no_strands` **the control.** Everything above except the strands, and
   it is a pot again. This is what proved the strands carry it.
7. `07_crown_tufts_rejected` sharpened crown. Rejected: reads as notches cut into
   the hair, and the reference's crown is smooth anyway.
8. `08_shipped` 05 with the lock length and fade settled.

**Legs**, in `legs/`:

1. `01_cone_as_committed` 1.55 thigh to 0.55 ankle, a two-to-one cone.
2. `02_straight_tube` no taper at all. Beats the cone, which was the useful
   finding: the thigh was not too wide, the shin was too thin.
3. `03_measured` measured off `ref/satoshi.png`: 1.42 / 1.03 / 1.01 / 0.85 at
   thigh / knee / calf / ankle.
4. `04_measured_slim` the same with a 1.26 thigh instead of 1.42. Won on
   preference: the reference's leg sits on a hip wider than this skeleton's, so
   the full measurement came out heavy here.
5. `05_shipped` 04's widths, hung so the outer edge of the thigh lands on the
   hip, plus the boot from `boots/03`. 04 still overhangs the body's side there
   and carries the intermediate boot.

`targets/` is byte-identical to what `./render.sh --preset ...` writes, checked.

**Boots**, in `boots/`: the foot used to be a multiple of the ankle, so it
doubled the moment the leg stopped tapering to a point. `02` is the intermediate
where the shaft came out wider than the foot and the boot narrowed going down;
`03` shipped, with the foot measured off the leg instead.
"""


if __name__ == "__main__":
    do_hair()
    do_legs()
    do_rest()
    reset()
    os.makedirs(f"{OUT}/committed_baseline", exist_ok=True)
    for n in ("satoko", "satoko_real", "satoshi", "satoshi_real"):
        for ext in ("png", "svg"):
            open(f"{OUT}/committed_baseline/{n}.{ext}", "wb").write(
                open(f"{SP}/base/{n}.{ext}", "rb").read()
            )
    open(f"{OUT}/README.md", "w").write(INDEX)
    n = sum(len(f) for _, _, f in os.walk(OUT))
    print(f"wrote {n} files under out/variants/")
    for d, _, f in sorted(os.walk(OUT)):
        if f:
            print(f"  {os.path.relpath(d, ROOT)}/  ({len(f)} files)")
