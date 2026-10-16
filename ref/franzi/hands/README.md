# Franzi hand and foot references

Close-up references of hands and feet, made for tracing when building the parametric SVG hands and feet in anime-character-creator. They exist because the hands in the full-body references (`ref/franzi/`) are only about 100 px tall and partly curled, so they are not traceable.

## How they were made
Each image is a Grok Imagine (web, Image mode) edit of the full-body bikini reference (`ref/franzi/04-bikini-fullbody`), so skin tone and drawing style match Franzi. Each prompt asked for a close-up on a plain black background, front view, same anime style. One image per prompt, no regenerations.

| File | Content | Notes |
|---|---|---|
| `open-palm.png` | Open palm facing the camera, five fingers spread, thumb out, wrist visible | Cleanest hand; best for finger lengths and palm shape |
| `relaxed.png` | Relaxed hand, side view, thumb toward camera, fingers curled | Plausible; fingers overlap |
| `fist.png` | Loose fist, wrist visible | Thumb lies along the side instead of wrapping over the fingers |
| `pointing.png` | Index finger pointing at the camera | Heavily foreshortened; curled fingers hard to read; no wrist. Rough guide only |
| `feet-front.png` | Both bare feet from the front, ankles to mid-shin | Five toes each; clean |
| `foot-top.png` | One foot seen from above, with ankle and some shin | Five toes; plausible right foot |

## Processing
- Backgrounds removed by script (near-black regions flood-filled and removed, 1 px feather), so PNGs are transparent.
- All images share one 1008x1792 canvas, unscaled. They are **not** scaled to the full-body references (a larger hand is the point), only to each other.
- `segments/<name>/` holds Grok's own segment cut-outs (Segments > Download All) for each image, e.g. fingers, fingernails, thumb, wrist, toes. Not every image has the same segments.
- `originals/` holds the untouched Grok JPEGs on black.

## Caveats
Sizes are not comparable to the body references. Hand proportions (finger length ratios) come from one generation each; check them against real anatomy when tracing. SFW only. AI-generated; original character, same licence as the repo (MIT).
