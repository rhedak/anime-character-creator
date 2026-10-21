# Risa adult reference images (front view)

Reference images of **Risa** on **Franzi's adult body**, with a smaller bust (A/B cup).
She has long straight dark red hair with bangs, green eyes, and a gold hair clip.
They exist so Risa can move onto that body. Her current code-drawn body was traced
from a clothed reference, which left body problems, including a neck that is too long.
The "Tall and Slender" body is to be deprecated later. This folder only holds the images.

They were made with Grok Imagine by editing Franzi's base. `02` to `07` are tracing references for the single clothing
pieces, edited in Grok Imagine from the uniform and bikini references. All images are
**1312 x 1504 px**, the same pixel grid, with no rescale between the opaque image and its cutout.

## Files

Numbered names follow `ref/franzi/` (`00` is the base, then the clothed variant).
The opaque files are the approved images. Each `-transparent` file is an RGBA cutout of the file beside it.

| file | what |
|---|---|
| `00-bikini.png` | the base: a white bikini on a black background, lossless PNG of the approved image |
| `00-bikini-transparent.png` | the same image, RGBA, transparent background |
| `01-school-uniform.png` | the same Risa in her usual school uniform, on a white background |
| `01-school-uniform-transparent.png` | the uniform image, RGBA, transparent background |
| `02-uniform-no-blazer.png` | the uniform without the blazer, on a white background |
| `03-uniform-no-ribbon.png` | the blouse without the ribbon, with skirt, socks and loafers, on a white background |
| `04-uniform-barefoot.png` | the uniform without the blazer, socks or shoes, on a white background |
| `05-blazer.png` | the blazer laid flat, no person (the shirt collar and ribbon show inside), on a white background |
| `06-blouse-bikini.png` | the blouse with the bikini bottom, on a black background |
| `07-skirt-bikini.png` | the skirt with the bikini top, on a black background |
| `02-...` to `07-...-transparent.png` | each of those images, RGBA, transparent background |
| `segments/<image>/...png` | Grok Imagine "Segments" layers (hair, eyes, hair clip, clothing parts, loafers, `anime-girl.png` = body silhouette) as **full-canvas transparent PNGs**, registered pixel-exactly to the image of the same name |
| `segments-composite-check.png` | the segments of each image composited over magenta (body silhouette left out), bikini left, uniform right |
| `segments-composite-check-02-07.png` | the same for `02` to `07`, in number order, three per row |

The uniform is a navy blazer with gold buttons, a white shirt, a light blue ribbon bow,
a blue-grey pleated skirt, black knee socks, and brown loafers.

## Segments

Segment layers are full-canvas (the same 1312 x 1504 as the image), so no offset file is needed: load a layer and
draw it at (0,0) over its image. Skin has no segment (Grok does not segment skin). `anime-girl.png` is the whole
figure silhouette, the counterpart of Franzi's `woman.png`. Grok gave one only for the bikini; **the uniform has no
full-body layer**. Grok's `black-background.png` layer was skipped, and the uniform had no background layer.
Segment names are Grok's:

- `00-bikini`: `anime-girl`, `long-red-hair`, `green-eyes/green-eyes-1..3`, `hair-clip`, `white-bikini-top`, `white-bikini-bottom`
- `01-school-uniform`: `red-hair`, `green-eyes/green-eyes-1..3`, `hair-clip`, `school-blazer`, `white-collared-shirt`, `blue-ribbon`, `pleated-skirt`, `brown-loafers/brown-loafers-1..2`
- `02-uniform-no-blazer`: `anime-girl`, `long-red-hair`, `green-eyes/green-eyes-1..3`, `hair-clip`, `white-collared-shirt`, `blue-ribbon`, `blue-pleated-skirt`, `black-knee-high-socks/black-knee-high-socks-1..3`, `brown-loafers/brown-loafers-1..2`
- `03-uniform-no-ribbon`: `anime-girl`, `long-red-hair`, `green-eyes/green-eyes-1..3`, `hair-clip`, `white-collared-shirt`, `blue-pleated-skirt`, `black-knee-high-socks/black-knee-high-socks-1..3`, `brown-loafers/brown-loafers-1..2`
- `04-uniform-barefoot`: `red-hair`, `green-eyes/green-eyes-1..3`, `hair-clip`, `white-collared-shirt`, `blue-ribbon`, `blue-pleated-skirt`, `bare-feet/bare-feet-1..2`
- `05-blazer`: `navy-blazer`, `white-collared-shirt`, `blue-ribbon-bow`, `gold-buttons/gold-buttons-1..3`, `breast-pocket/breast-pocket-1..3`, `flap-pockets/flap-pockets-1..3`
- `06-blouse-bikini`: `red-hair`, `green-eyes/green-eyes-1..3`, `hair-clip`, `white-collared-shirt`, `blue-ribbon`, `white-panties` (Grok's name for the bikini bottom)
- `07-skirt-bikini`: `red-hair`, `green-eyes/green-eyes-1..3`, `hair-clip`, `white-bikini-top`, `blue-pleated-skirt`

`green-eyes-1` covers both eyes in the bikini image and `green-eyes-3` does in the uniform one; the other two eye layers
are single eyes and overlap it. `white-collared-shirt` is mostly hidden under the blazer, so only its visible parts are opaque.
In `05-blazer`, `breast-pocket-1..2` and `flap-pockets-1..2` are the same two lower pockets, and `breast-pocket-3` and
`flap-pockets-3` are both the breast pocket: Grok made each pocket twice under two names.

**How they were made**: Grok Imagine, *Segments > Download All*, on each of the approved images. Grok delivers each
layer cropped to its own bounding box, so each was located in its image by masked template matching (squared difference
on the layer's opaque pixels, as in `ref/franzi/scripts/01_locate_segments.py`) and pasted unchanged onto a transparent
1312 x 1504 canvas. Every layer's best match has an RMS colour error of 0.11 or less.

**Verification**: every layer's mean RGB difference to the opaque image, over the layer's solid pixels (alpha > 250),
is **0.00**, and the segments composited back give 0 differing pixels within their coverage. Most layers have 0 to 15 px
(alpha > 127) outside the image's `-transparent` cutout, at the edges. The hair layers are the exception: `long-red-hair`
5,558 px (and `anime-girl` 4,118 px, the same places), `red-hair` 2,216 px. Grok counts the background seen through gaps between
hair strands as hair (near-black in the bikini image, white in the uniform one), while the cutout makes those gaps
transparent. The layers were left as Grok made them.

For `02` to `07` the same checks hold: all 64 layers have a mean RGB difference of **0.00** and a best-match RMS of 0.11 or
less, and each composite gives 0 differing pixels within its coverage. Outside the cutout, the hair layers again have the
most (2,303 to 7,438 px, `anime-girl` about 3,000 px), `white-collared-shirt` and `blue-pleated-skirt` up to 166 px, and the
rest 0 to 90 px.

## Caveats

- Her loafers are cut off at the bottom edge of the uniform source (and of `02` and `03`). That crop is accepted.
- `06` and `07` are framed closer, head to thighs, so Risa is drawn larger there than in the other images.
- Front view only. The bikini figure stands on black. The uniform figure stands on white. `06` and `07` are on black, `02` to `05` on white.
- SFW: an adult figure in a bikini, a school uniform, or parts of both.

## Licence and AI note

Risa is an original character. These images are released under the same **MIT licence as the repository**.
They were generated with AI (Grok Imagine). The copyright status of AI-generated images is not settled in every jurisdiction.
