# Franzi reference images (front view, neutral pose)

Reference images of **Franzi**, an original, adult (21+) anime character, for tracing a
proper adult body and clothing in the code-drawn creator. They are a **SFW swimwear /
underlayer study**: the point is to see the body shape under the dirndl, not to depict it.
Proposed repo location: `ref/franzi/` (next to `ref/katherina/`, which also holds Grok images
plus a `segments/` folder).

Hand and foot references: [hands/README.md](hands/README.md).

## Files

All five images share ONE canvas, **1312 x 2440 px, RGBA, transparent background**, so they overlay exactly
(see `overlay-check.png`). The head/eye position is the same in all of them.

| file | what | use |
|---|---|---|
| `00-base-dirndl.png` | the neutral base: white blouse, green bodice, red apron (head to mid-thigh) | style, face, hair, dirndl design |
| `01-swimsuit.png` | plain modest white one-piece swimsuit | torso/hip/leg silhouette, waist, bust line |
| `02-blouse.png` | white puff-sleeve blouse + plain short light shorts-style underlayer | blouse cut, sleeves, underlayer |
| `03-bodice.png` | white blouse + green laced bodice with gold buttons, no apron, short underlayer | bodice shape over the body |
| `04-bikini-fullbody.png` | plain two-piece white bikini, full body head to bare feet | full-body proportions, legs, feet (about 6.4 heads tall) |
| `segments/<image>/...png` | Grok Imagine "Segments" layers (hair, eyes, clothing parts, feet, buttons, `woman.png` = body silhouette) as **full-canvas transparent PNGs**, registered pixel-exactly to the image of the same name | tracing single parts (hair shape, bodice, sleeves, feet) |
| `originals/*-unscaled.png` | the same five images, background removed but at the source pixel grid (ref-4 is 1008x1792, not scaled) | if you need unresampled pixels |
| `canvas.json` | canvas size, ref-4 scale and offset | |
| `verification.json` | alignment numbers (see below) | |
| `overlay-check.png` | all five at 45% in different colours (full figure + 1:1 head crop) | proof of alignment |
| `preview-sheet.png`, `segments-composite-check.png` | contact sheets on grey / segments over magenta | quick look |
| `scripts/` | everything used to produce the above (see below) | |

Segment layers are full-canvas (same 1312x2440 as the image), so no offset file is needed; load a layer and
draw it at (0,0) over its image. Skin has no segment (Grok does not segment skin); `woman.png` is the whole
figure silhouette where Grok provided it (swimsuit, bodice, bikini; none for the blouse). Grok's
`black-background.png` layers were skipped. Segment names are Grok's (`black-hair`, `brown-eyes/...`,
`white-one-piece-swimsuit`, `green-corset`, `lace-up-front/...`, `puffed-sleeves/...`, `gold-buttons/...`, `white-shorts`,
`beige-shorts`, `white-blouse`, `white-bikini-top`, `white-bikini-bottom`, `bare-feet/...`). The eyes are brown in most
images but yellow-ish in the blouse one (`yellow-eyes`), which is a Grok drift, not a design choice.
Source-pixel offsets of every segment are in `scripts/seg_offsets_full.json` (all matched the source JPG with RMS colour error ~0).

## How they were made

1. **Base**: `franzi-neutral` made with Grok Imagine (dirndl, neutral standing pose, black background).
2. **References 1-4**: each an *edit of the base* in Grok Imagine, prompt form:
   `Same character, same face, same hair, same framing, same black background, same art style, same neutral standing pose... replace the dirndl with <X>`
   with `<X>` being:
   - ref 1 swimsuit: `plain modest one-piece swimsuit (solid white or light colour)`
   - ref 2 blouse: `white puff-sleeve blouse with scalloped square neckline and plain short light-coloured shorts-style underlayer, no dirndl bodice/apron`
   - ref 3 bodice: `white blouse + green dirndl bodice with front lacing and gold buttons, no apron, plain short underlayer`
   - ref 4 bikini: `plain fitted two-piece bikini, simple triangle top fully covering chest, matching bottoms, full body head to feet`
   (the first three keep the 1312x1504 framing, head to mid-thigh; ref 4 came out 1008x1792 with feet.)
3. **Segments**: Grok Imagine, *Segments > Download All*, for refs 1-4 (none for the base).
4. **Scripts** (run in order, `scripts/`):
   - `alpha_original.py`: the original black-background removal logic (border-connected near-black flood fill, enclosed pure-black gaps >=150 px, 1 px feather, decontaminate against black). Reference copy; not run directly (it was written for the earlier pack and has hard paths).
   - `01_locate_segments.py`: finds each segment's (x,y) in its source JPG by masked template matching -> `seg_offsets_full.json` (also locates the 16 gold buttons that the earlier analysis had no offset for).
   - `02_remove_bg.py`: runs that logic, then **unions the mask with the Grok segment alphas** (hair, clothes, eyes, feet) because the hair is black and the threshold eats ~1,100-1,700 px of hair edge / enclosed hair-black per image. Base has no segments; its mask is the plain flood fill (hair-fix added 2 px, i.e. nothing was lost).
   - `03_scale_search.py` (reads the intermediate unscaled PNGs that 02 writes to `work/orig/`, not shipped; they equal `originals/`): picks the ref-4 scale/offset (see below).
   - `04_build_canvas.py`: builds the common canvas, scales ref-4 (premultiplied Lanczos) and pushes segments through the same transform.
   - `05_verify.py`, `06_previews.py`: checks and preview images.
   - `analysis/`: the earlier measurement scripts and data (`measure.py`, `step2-4.py`, `measurements.json`, `SUMMARY.md`...).

**Scale of ref 4**: x**1.365**, pasted at (-34, -6) on the canvas (ref-4 is cropped by 34 px on the left of the scaled image;
that is empty black background). Pupil distance alone gives 1.346 (eye-aligned head IoU 0.96); a brute-force fit of the head
silhouette against base/1/2/3 gives 1.365 (head IoU 0.986), which is what is used. Eye lines then agree to about +-2 px.
The other four are unscaled at (0,0); their eye lines differ by up to 2.6 px among themselves (Grok edits are not pixel-identical).

## Measured proportions

H = head height (top of hair to chin), measured on the pre-scale images (`scripts/analysis/measurements.json`; chin is +-8 px uncertain).

| image | H px | head width / H | shoulder span / H | waist width / H | hip width / H | crotch below chin (H) | pupil distance / H |
|---|---|---|---|---|---|---|---|
| base dirndl | 355 | 0.85 | 1.50 (puff sleeves) | n/a | n/a | n/a | 0.32 |
| 1 swimsuit | 352 | 0.86 | 1.26 (bare shoulders) | 0.69 | 1.23 | 2.29 | 0.32 |
| 2 blouse | 351 | 0.86 | 1.51 (puff sleeves) | 0.71 | 1.32 (blouse flare) | 2.30 | 0.32 |
| 3 bodice | 350 | 0.86 | 1.51 (puff sleeves) | 0.69 | 1.25 | 2.25 | 0.33 |
| 4 bikini | 256 | 0.86 | 1.24 (bare shoulders) | 0.67 | 1.16 | 2.22 | 0.33 |

Roughly: head about 1/6.4 of full height (ref 4: head top to sole = 6.4 H), neck base 0.14-0.18 H below chin, shoulders about 1.25 H, waist about 0.69 H,
hips about 1.2 H, crotch about 2.25 H below the chin, hands end about 2.6 H below the chin.

## Verification (also in `verification.json`)

- Head-silhouette IoU between any two of the five on the canvas (y < 445): 0.980 - 0.994 (mean-of-pairs for ref 4 vs the rest 0.980-0.991).
- Full silhouette IoU (y < 1504, clothing differs, so lower): base vs 1/2/3/4 = 0.88/0.92/0.90/0.84; 2 vs 3 = 0.97.
- Every segment layer: mean RGB difference to the opaque pixels of its image 0.00-0.08 (refs 1-3, exact), 0.2-0.9 for ref 4 (resampling); no layer failed, 0 to 18 px of alpha outside the image.
- Visual checks on white and magenta: head/hair edges and shoulders of all five, 1:1 and 4x zoom; segments composited back over magenta.

## Caveats

- Ref 4 is a separate generation at another framing: arms hang about 0.05-0.1 H closer to the body, hips are about 5-7% narrower,
  legs and ankles thinner than ref 1-3 imply. Prefer ref 1-3 for torso/hip width, ref 4 for leg length, feet and total height.
- Eyes drift: Grok labelled the eyes brown in refs 1, 3, 4 and yellow in ref 2 (colour differs slightly between images).
- The swimsuit is high-cut (reads as high-cut one-piece); the blouse in ref 2 is buttoned in front, unlike the dirndl blouse.
- A very thin dark line may remain on the outer edge of the white clothes (JPEG ringing on the black background); hair edges are clean.
- Bottom edges of base/1/2/3 are the crop at mid-thigh (y = 1504); the base's skirt is cut there.
- Front view, neutral pose only. Side and back views are planned later.

## Licence and AI note

Franzi is an original character; these images are released under the same **MIT licence as the repository**.
They were generated with AI (Grok Imagine); the copyright status of AI-generated images is not settled in every jurisdiction.

**SFW**: all figures are adults, clothed in swimwear or underlayer (one-piece, bikini, shorts, blouse), no nipples or genitals shown,
in line with the repository README rule that nothing under 21 is rendered nude.
