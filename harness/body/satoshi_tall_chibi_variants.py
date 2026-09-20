"""Render candidate `tall_chibi`-family body profiles for T2b
(`docs/satoshi-tall-chibi-plan.md`): a look, not a metric. Writes PNGs to
`out/body_variants/` for the owner to compare by eye, on both Satoshi (who
the new reference is of) and Katherina (who the current `tall_chibi` was
measured off), since a profile that only looks right on one of them is not a
fix.

Candidates:
  baseline   today's `tall_chibi`, unchanged (T1's headroom fix applied).
  heads_only today's `tall_chibi` landmarks, only `heads` bumped from 3.47 to
             the reference's measured ~3.98 (rounded to 4.0): tests whether
             a taller/leaner head-to-body ratio alone, with no other shape
             change, closes most of the gap.
  measured   a profile solved from `satoshi_tall_chibi_landmarks.py`'s
             numbers: heads, shoulder_y, waist_y, an approximate hip_y (the
             crotch, the only visible pelvis-adjacent landmark on a
             trouser-wearer), ankle_y, waist_half_w, leg_half_w. hem_y and
             hem_half_w are left unmeasured (None, keep the base lerp):
             `tall_chibi`'s hem is a skirt hem, which has no equivalent on
             a straight trouser leg.
"""

import dataclasses
import os

import cairosvg

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, BodyProfile, build_skeleton

os.makedirs("out/body_variants", exist_ok=True)

MEASURED = BodyProfile(
    heads=3.98,
    shoulder_y=0.965,
    waist_y=2.628,
    hip_y=2.762,
    ankle_y=5.669,
    waist_half_w=0.59,
    leg_half_w=0.253,
)
HEADS_ONLY = dataclasses.replace(c.BODY_TYPES["tall_chibi"], heads=3.98)

CANDIDATES = {
    "baseline": c.BODY_TYPES["tall_chibi"],
    "heads_only": HEADS_ONLY,
    "measured": MEASURED,
}


def render(preset_name, profile_name, profile):
    p = PRESETS[preset_name]
    margin = c.hat_hair_margin(p)
    margin = max(margin, c.default_hair_margin(BUILDS["chibi"]))
    sk = build_skeleton(heads=profile.heads, frame=p.frame, min_hair_margin=margin)
    chibi_build = build_skeleton(heads=p.heads, frame=p.frame).build
    sk = profile.applied(sk, chibi_build)
    svg = c.render_character(p, sk)
    out = f"out/body_variants/{preset_name}_{profile_name}"
    open(f"{out}.svg", "w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{out}.png")
    print("wrote", out)


for preset_name in ("satoshi", "katherina"):
    for profile_name, profile in CANDIDATES.items():
        render(preset_name, profile_name, profile)
