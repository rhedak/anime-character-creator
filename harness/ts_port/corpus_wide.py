"""A wide, seeded corpus of CharacterParams for numeric recording.

`corpus()` yields CharacterParams. Parameter sets that fail to construct (the
dataclasses validate in __post_init__) are not yielded; they are counted in
`STATS["construct_errors"]` keyed by exception type and message, because they
are data about the validation edge, not failures of the harness.

Everything is drawn from `random.Random(SEED)`, so the sequence is the same on
every run. Callers render each yielded value with id_prefix "" and "x".
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import replace

SEED = 12345
RANDOM_CASES = 400
STATS: dict = {"construct_errors": Counter(), "yielded": 0, "groups": Counter()}


def _try(group, build):
    """Build one params value, counting a construction error instead of raising."""
    try:
        p = build()
    except Exception as e:  # data, not a failure
        STATS["construct_errors"][f"{type(e).__name__}: {str(e)[:100]}"] += 1
        return None
    STATS["groups"][group] += 1
    return p


def corpus():
    import anime_character_creator as A
    from anime_character_creator import catalogue as C
    from anime_character_creator.character import HAIRSTYLES, FINISHES

    STATS["construct_errors"].clear()
    STATS["groups"].clear()
    STATS["yielded"] = 0
    rnd = random.Random(SEED)
    cat = C.build_catalogue()
    bases = list(A.PRESETS.values()) + list(A.NEUTRAL_BASES.values())

    def out(group, build):
        p = _try(group, build)
        if p is not None:
            STATS["yielded"] += 1
            return [p]
        return []

    # 1. every base, flat and soft
    for p in bases:
        for fin in FINISHES:
            yield from out("base", lambda p=p, fin=fin: replace(p, finish=fin))

    # 2. every hairstyle, flat default length and soft with a longer length
    for p in bases:
        for h in sorted(HAIRSTYLES):
            yield from out("hairstyle", lambda p=p, h=h: replace(p, hairstyle=h))
            yield from out("hairstyle_soft_long", lambda p=p, h=h: replace(p, hairstyle=h, finish="soft", hair_length=0.75))

    # 3. heights and ages (catalogue range ends plus values just outside)
    heights = sorted({cat["height"]["min"], cat["height"]["max"], 0.8, 0.85, 0.9, 1.1, 1.25, 1.3, 0.75, 1.4})
    ages = sorted({cat["face_age"]["min"], cat["face_age"]["max"], 0.0, 0.5, 0.9, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 21, 25, 30, 40})
    for p in bases:
        for ht in heights:
            yield from out("height", lambda p=p, ht=ht: replace(p, height=ht))
        for fa in ages:
            yield from out("face_age", lambda p=p, fa=fa: replace(p, face_age=fa))

    # 4. expressions applied to the bases, 5. every body type
    for p in bases:
        for _name, ex in sorted(A.EXPRESSIONS.items()):
            yield from out("expression", lambda p=p, ex=ex: ex.applied_to(p))
        for body in cat["bodies"]:
            yield from out("body", lambda p=p, body=body: replace(p, body=body["id"]))

    # 6. one-at-a-time sweeps, including values outside the catalogue range
    sweep_vals = (-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
    for p in bases:
        for k in ("bust", "chest", "waist_shift", "frame", "hair_tail", "hair_length", "highlight_strength", "right_arm_out", "left_arm_out"):
            for v in sweep_vals:
                yield from out("sweep_" + k, lambda p=p, k=k, v=v: replace(p, **{k: v}))
        for hs in [h["id"] for h in cat["hand_styles"]]:
            for gs in [g["id"] for g in cat["grip_styles"]]:
                yield from out("hands", lambda p=p, hs=hs, gs=gs: replace(p, hand_style=hs, grip_style=gs))

    # 7. seeded random combinations drawn from the catalogue ranges
    def val(r):
        lo, hi = r["min"], r["max"]
        span = hi - lo
        mode = rnd.random()
        if mode < 0.25:
            return lo + span * rnd.random()
        if mode < 0.5:
            step = rnd.choice([0.05, 0.1, 0.25, 0.01])
            n = max(int(span / step), 1)
            return round(lo + step * rnd.randint(0, n), 4)
        if mode < 0.8:
            return rnd.choice([lo, hi, (lo + hi) / 2])
        # out-of-range extremes
        return rnd.choice([lo - 0.1 * span, hi + 0.1 * span, lo - span, hi + span, 0.0, -1.0, 1.0])

    def col():
        return "#%02x%02x%02x" % (rnd.randrange(256), rnd.randrange(256), rnd.randrange(256))

    ranged = ("height", "face_age", "hair_length", "hair_tail", "waist_shift", "bust", "chest", "highlight_strength")
    for _ in range(RANDOM_CASES):
        base = rnd.choice(bases)
        face = {}
        for r in cat["face"]["ranges"]:
            if rnd.random() < 0.5:
                face[r["field"]] = val(r)
        for b in cat["face"]["bools"]:
            if rnd.random() < 0.3:
                face[b["field"]] = rnd.random() < 0.5
        for s in cat["face"]["selects"]:
            if rnd.random() < 0.5:
                face[s["field"]] = rnd.choice(s["options"])["value"]
        outfit = {}
        for g in cat["garments"]:
            if rnd.random() < 0.6:
                outfit[g["color"]["field"]] = col()
                for r in g.get("ranges", []):
                    if rnd.random() < 0.6:
                        outfit[r["field"]] = val(r)
                for b in g.get("bools", []):
                    if rnd.random() < 0.5:
                        outfit[b["field"]] = rnd.random() < 0.5
                for s in g.get("selects", []):
                    if rnd.random() < 0.5:
                        outfit[s["field"]] = rnd.choice(s["options"])["value"]
        top = {}
        for k in ranged:
            if rnd.random() < 0.6:
                top[k] = val(cat[k])
        top["hairstyle"] = rnd.choice(cat["hairstyles"])["id"]
        top["body"] = rnd.choice(cat["bodies"])["id"]
        top["finish"] = rnd.choice(["flat", "soft"])
        for c in cat["colors"]:
            if not c["optional"] or rnd.random() < 0.4:
                top[c["field"]] = col()
        top["hand_style"] = rnd.choice([h["id"] for h in cat["hand_styles"]])
        top["grip_style"] = rnd.choice([h["id"] for h in cat["grip_styles"]])
        top["hair_knot"] = rnd.random() < 0.3
        top["frame"] = rnd.choice([0.0, rnd.uniform(-1, 1)])
        yield from out(
            "random",
            lambda base=base, face=face, outfit=outfit, top=top: replace(
                base, face=replace(base.face, **face), outfit=replace(base.outfit, **outfit), **top
            ),
        )


if __name__ == "__main__":
    import anime_character_creator as A
    from pathlib import Path

    assert Path(A.__file__).resolve().is_relative_to(Path(__file__).resolve().parents[2] / "src"), A.__file__
    n = sum(1 for _ in corpus())
    print("cases", n, "groups", dict(STATS["groups"]))
    for k, v in STATS["construct_errors"].most_common():
        print("  construct error", v, k)
