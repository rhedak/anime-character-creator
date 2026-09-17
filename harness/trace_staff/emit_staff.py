"""Emit the traced staff as character.py source; insert it before `def _arms(`.

Re-running replaces the previously emitted block (between the two marker lines).
"""

import json

SRC = "/Users/henrik/git/anime-character-creator/src/anime_character_creator/character.py"
OUT = "out/trace_staff"
BEGIN = "# A wizard's staff, traced per `.claude/skills/trace-reference/SKILL.md`"
data = json.load(open(f"{OUT}/staff_trace.json"))


def pt(p):
    return f"({p[0]:.3f}, {p[1]:.3f})"


def chain_rows(c, indent):
    pad = " " * indent
    rows = [f"{pad}{pt(c['start'])},", f"{pad}["]
    rows += [f"{pad}    ({pt(a)}, {pt(b)})," for a, b in c["segs"]]
    rows.append(f"{pad}],")
    return rows


def chain(name, c, comment):
    rows = [f"# {ln}" for ln in comment]
    rows.append(f"{name}: Chain = (")
    rows += chain_rows(c, 4)
    rows.append(")")
    return "\n".join(rows)


def chains(name, cs, comment):
    rows = [f"# {ln}" for ln in comment]
    rows.append(f"{name}: list[Chain] = [")
    for c in cs:
        rows.append("    (")
        rows += chain_rows(c, 8)
        rows.append("    ),")
    rows.append("]")
    return "\n".join(rows)


HEADER = f"""{BEGIN}
# from `../time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg`
# (`docs/katherina-accessories-plan.md`, milestone 3), on the witch hat's own
# calibration (173.7 px per head radius, head centre at (650, 481); see the
# comment above `_HAT_UNDERSIDE`). Every chain is in the reference's head radii,
# as the reference draws it; `_staff_placement` maps them onto this figure.
#
# The regions are the reference's own. The wood is every brown fill component
# the reference's outlines separate, unioned and closed, with the shaft carried
# straight across the rows the reference's fist hides (its edges measured just
# above and just below the fist and interpolated). The strands are the braid's
# and prongs' separate pieces: the same fills split at a darker threshold, which
# the structural lines between strands reach and the wood grain inside them does
# not; slivers under 800 px were dropped. The crystal is cut from its glow by
# colour, and its faces are three smoothed brightness bands, dark and light
# traced, the mid tone the crystal's own fill. Grain and the glow are texture and
# do not transfer.
_STAFF_GRIP: Point = {pt(data["grip"])}
_STAFF_TIP: Point = {pt(data["tip"])}
_STAFF_TOP_Y = {data["top_y"]:.3f}"""

parts = [HEADER]
parts.append(chain("_STAFF_WOOD", data["wood"], ["The whole wooden silhouette, prong tips to the foot of the shaft."]))
parts.append(chains("_STAFF_STRANDS", data["strands"], ["The prongs' and braid's strands, over the silhouette, each with its own line."]))
parts.append(chain("_STAFF_CRYSTAL", data["crystal"], ["The gem's outline."]))
parts.append(chains("_STAFF_FACETS_DARK", data["facets_dark"], ["Its two shadowed side faces."]))
parts.append(chains("_STAFF_FACETS_LIGHT", data["facets_light"], ["Its lit faces: the long one under the tip, and the wedge near the base."]))

FUNCS = '''

def _staff_placement(sk: Skeleton, p: CharacterParams) -> Callable[[Point], Point]:
    """Map the staff's reference head radii onto this figure's, as a point function.

    The grip goes to the centre of the hand holding it, and the staff divides
    there. Above the grip it keeps the reference's shape at one scale, the one
    that puts the top of the ornament at the reference's own height against the
    head (`_STAFF_TOP_Y`): at chibi that scale is close to 1, since the chibi's
    held-out hand sits almost where the reference's does. Below the grip the
    shaft keeps its lean and its width and is shortened (or lengthened) along its
    own axis only, so the foot lands on the ground: the reference's figure is
    about three and a half heads tall and this one's chibi is 2.4, so a staff
    carried at the reference's scale would stand a head and a half into the
    floor. Widths across the shaft take the upper scale everywhere, so the
    shaft does not change thickness at the hand. The shaft below the fist was
    smoothed before tracing, since that shortening bunches small knots into
    spikes.
    """
    hx, hy = __HAND_CENTRE__
    gx, gy = _STAFF_GRIP
    tx, ty = _STAFF_TIP
    length = math.hypot(tx - gx, ty - gy)
    ax, ay = (tx - gx) / length, (ty - gy) / length
    k_up = (hy - _STAFF_TOP_Y) / (gy - _STAFF_TOP_Y)
    ground = (sk.foot_y - sk.head_cy) / sk.head_r
    k_low = (ground - hy) / (ty - gy)

    def placed(pt: Point) -> Point:
        dx, dy = pt[0] - gx, pt[1] - gy
        along = dx * ax + dy * ay
        across = -dx * ay + dy * ax
        k = k_up if along <= 0 else k_low
        along *= k
        across *= k_up
        return (hx + along * ax - across * ay, hy + along * ay + across * ax)

    # The ornament reaches out past the hand, and a hat's headroom narrows the
    # canvas in head radii, so at chibi its outer prong lands on the canvas edge.
    # Slide the whole staff inward by exactly what keeps its outline on the page
    # (the chain's controls bound the curve), and by nothing when it already fits.
    start, segs = _STAFF_WOOD
    reach = min(placed(q)[0] for q in (start, *(q for seg in segs for q in seg)))
    edge = (-sk.canvas_w / 2 + _stroke_w(sk)) / sk.head_r
    shift = max(0.0, edge - reach)

    def xf(pt: Point) -> Point:
        x, y = placed(pt)
        return (x + shift, y)

    return xf


def _staff(sk: Skeleton, p: CharacterParams) -> str:
    """A wizard's staff held in the character's own right hand (the viewer's left).

    Drawn before the arms, so the hand closes over the shaft and the sleeve
    passes in front of it, and after the hair and every garment, so the staff is
    in front of the body it is held beside. Back to front: the wooden silhouette,
    its strands, then the crystal: mid tone, dark and light faces, and its
    outline last so the faces stay inside it.
    """
    wood = p.outfit.staff_color
    if wood is None:
        return ""
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    sw = _stroke_w(sk)
    xf = _staff_placement(sk, p)

    def d(chain: Chain) -> str:
        start, segs = chain
        return _curve(cx, cy, r, xf(start), [(xf(c), xf(e)) for c, e in segs])

    parts = [f'<path d="{d(_STAFF_WOOD)}" fill="{wood}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />']
    parts.extend(
        f'<path d="{d(strand)}" fill="{wood}" stroke="{OUTLINE}" stroke-width="{sw * 0.6:.1f}" '
        'stroke-linejoin="round" />'
        for strand in _STAFF_STRANDS
    )
    crystal = p.outfit.staff_crystal_color
    if crystal is not None:
        parts.append(f'<path d="{d(_STAFF_CRYSTAL)}" fill="{crystal}" />')
        dark = shade(crystal, value_factor=0.88, saturation_boost=1.10)
        light = shade(crystal, value_factor=1.03, saturation_boost=0.54)
        parts.extend(f'<path d="{d(face)}" fill="{dark}" />' for face in _STAFF_FACETS_DARK)
        parts.extend(f'<path d="{d(face)}" fill="{light}" />' for face in _STAFF_FACETS_LIGHT)
        parts.append(
            f'<path d="{d(_STAFF_CRYSTAL)}" fill="none" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'
        )
    return "".join(parts)
'''

END = "# (end of the traced staff)"


def main(hand_centre_expr: str) -> None:
    block = "\n\n".join(parts) + "\n" + FUNCS.replace("__HAND_CENTRE__", hand_centre_expr) + "\n\n" + END + "\n"
    src = open(SRC).read()
    if BEGIN in src:
        a = src.index(BEGIN)
        b = src.index(END) + len(END) + 1
        src = src[:a] + block + src[b:]
    else:
        anchor = "def _arms(sk: Skeleton, p: CharacterParams) -> str:"
        assert src.count(anchor) == 1
        src = src.replace(anchor, block + "\n\n" + anchor)
    open(SRC, "w").write(src)
    print("emitted")


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
