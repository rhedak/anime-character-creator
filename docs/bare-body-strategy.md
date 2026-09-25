# Bare body strategy

How to work this campaign. Everything in `bust-strategy.md` applies (predict
before measuring, one change per measurement, measure the drawn ink, look in
the right view, only the owner signs off); this file adds what is particular
to showing the body.

## Procedure

1. **Clothed output is the control.** Every preset wears a tunic and boots,
   so a change for the bare figure must leave `ref-out/` byte-identical. Run
   `./refresh-ref-out.sh --check` after every change; a diff is a leak.
2. **Draw bare-only parts only when bare.** A base top drawn under a tunic
   costs no visible pixel but changes every SVG's bytes, and then the control
   above is lost. Gate on the garment's absence.
3. **Judge in two views**: the mannequin (adults, nothing worn,
   `harness/bare/mannequin.py`) for the body's shape, the base-layer sheet
   (the cast, tunic off) for what the tool will show.
4. **Adults only in the mannequin.** No bare render of Katherina or Linnea,
   or any preset whose age is not an adult's, in any view.
5. **Chibi first.** The realistic build must render without error; it is not
   judged here.

## Anti-patterns, with the incident behind each

- **Judging the body through a garment's leftover outline.** The audit's
  first sheet had the tunic unfilled but still stroked, and the bust read
  because the tunic's outline drew it. With the tunic truly gone (step 2) the
  women read flat: the bust over the arms was the garments', never the
  body's. Look at the mannequin, not a half-removed garment.
