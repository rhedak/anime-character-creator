# Web GUI plan

Plan for a browser-based character creator that a non-technical visitor
can use without installing anything, hosted free and permanently.
Written 2026-08-10 at `826e308` "add kristas goggles". The plan below
predates the build; the page it describes is now live, see "What has
to be built" at the bottom for what shipped and `web/` for the code.

## What is being built

A single web page holding a limited set of choices: pick a character,
change colours, and swap between the hairstyles and garments that
already exist in the generator. Download the result. Not a full
parameter editor, and deliberately not one. Anyone who wants every knob
can clone the repository, which is public and permissively licensed, and
that is the intended escape hatch rather than a failure of the tool.
Which permissive licence is currently ambiguous, which the licensing
section below deals with.

The audience is people who will never open a terminal. That single fact
drives most of what follows.

## Where the Python runs, and why that is the whole decision

The question this started from was which hosting service runs the Python
for free. That question dissolves on inspection, and the dissolution is
the plan.

`pyproject.toml` declares `dependencies = []`. The entire render path
imports `math`, `colorsys`, `dataclasses` and `collections.abc`, all
standard library. It opens no files, touches no network, holds no
secrets and needs no database. `render_character()` takes a params
struct and returns a string. Measured on this machine, one chibi
character takes **0.47ms** and produces **16KB of SVG**. `cairosvg` is an
optional extra used only to rasterize that text to PNG, which is why
`pyproject.toml` already keeps it out of `dependencies`.

There is no work here for a server to do. So the plan is:

**GitHub Pages serves static files. The visitor's own browser runs the
real Python, via Pyodide, on their own CPU.**

Pyodide is CPython compiled to WebAssembly. The browser downloads it and
executes it in the tab, at close to native speed, in the same sandbox
that runs ordinary JavaScript. The package is pure Python with no
dependencies, so it needs no wheel, no `micropip` and no build step
beyond copying `src/anime_character_creator/` into the served folder.
The same `character.py` that gets edited in this repository is the one
that runs in the visitor's browser.

The visitor needs nothing installed. Pyodide *is* the Python; it does
not look for a local interpreter. A machine that has never had Python on
it runs this fine. Worth stating plainly because it inverts the usual
constraint: shipping this as a Python script would require every user to
have Python, `uv` and the right version, which excludes essentially the
whole intended audience. The browser version removes that requirement
rather than adding one.

## What GitHub Pages does and does not do

It is a file server on a CDN with no compute attached. It hands over the
bytes of the program; it never executes the program. Closer to a
bookshelf than to a web service.

The consequences are what make this attractive:

| | Browser (this plan) | Any server tier |
| --- | --- | --- |
| Runs `render_character` | The visitor's CPU | A rented CPU |
| Latency per change | ~0.5ms, local | 20 to 200ms, plus cold start |
| Cost at 100,000 users | Nothing | Not nothing |
| Uptime owed to anyone | None | Real |
| Data leaving the visitor | None, ever | Every parameter they touch |
| Works offline after first load | Yes | No |

The scaling row is the counterintuitive one. There is no shared resource
to exhaust, because every visitor brings their own interpreter.

## What was rejected

**Porting the renderer to JavaScript.** The obvious answer, and wrong
here for one reason that outweighs everything in its favour:
`character.py` is 4,744 lines and is the single source of shape truth.
A JavaScript copy means every future hairstyle is written twice, and the
two copies drift silently, which is precisely the failure this project's
architecture exists to prevent. `CLAUDE.md` says shapes are
skeleton-relative so proportions can change globally without rewriting
every part; a second implementation gives that up.

**Transpiling the Python to JavaScript** (Transcrypt and similar). Same
drift, less visible, plus a fragile build step over 6,568 lines of code
that leans on dataclasses and frozen instances.

**A free server tier.** Considered and rejected individually:

- *Hugging Face Spaces.* The only free tier taken seriously here: no
  card required, and Gradio supplies a UI for nothing. Rejected on two
  counts. It sleeps when idle and wakes slowly, and a project whose
  headline is that no AI image generation is involved anywhere should
  not be hosted on the model-demo site. The association undoes the point.
- *Render.* Free web services spin down after inactivity and cold-start
  in tens of seconds, which is the worst possible behaviour for a link
  someone clicks out of curiosity.
- *Vercel and Netlify functions.* Both run Python and both work. Their
  free tiers restrict non-personal use, and they would be paying in
  complexity for something the browser already does better.
- *Google Cloud Run.* Scales to zero and has a real free allowance, but
  requires a billing account, which means attaching a card to a toy.

None of these were rejected on price. They were rejected because a
server adds cost, cold starts, an availability commitment and an abuse
surface, and buys nothing in return.

## How a visit works

1. The browser requests the page from GitHub's CDN and receives HTML,
   CSS, a little JavaScript, the `.py` files as plain text, and the
   pre-rendered preset SVGs.
2. **A character is on screen immediately**, as a static SVG. No Python
   has run yet.
3. Pyodide downloads in the background. This is where the megabytes go.
4. Pyodide boots CPython in the tab with an in-memory virtual
   filesystem. The JavaScript writes the package into it and imports it.
5. The visitor moves a control. JavaScript calls `render_character()`,
   which runs locally in about half a millisecond and returns the SVG
   string.
6. That string goes into the page. Steps 5 and 6 repeat with **no
   network traffic at all**.

Step 2 is what hides the one real cost. Anyone who arrives, looks, and
leaves never waits for anything.

## What happens when it fails

Four things can go wrong, in descending order of likelihood:

**A corporate network or content blocker blocks the CDN.** The most
realistic and the most often overlooked. Mitigated by self-hosting the
Pyodide runtime on the Pages site as a fallback when the CDN request
fails.

**A cheap or old phone.** It works, but boot can take ten seconds or
more, and under memory pressure the browser may kill the tab.

**A browser with no WebAssembly.** Internet Explorer and forgotten
tablets. WebAssembly support sits around 97 to 98 percent of browsers in
use, and the missing slice is not an audience this is for.

**JavaScript disabled.** Then nothing works, as on nearly every site.

In every one of those cases the page still shows all fourteen characters
and still lets them be downloaded, because those are static files that
never needed Python. What is lost is the ability to change anything. The
page should detect the failure, say so in one line, and link to the
repository. That floor is better than the server-backed equivalent,
where a failure is an error page and nothing else.

## Step zero, and what would falsify this plan

**The in-browser import has not been verified.** Everything above is
reasoning from `dependencies = []` and from the imports actually present
in the package. It has not been run, because this machine has no browser
and no route to the Pyodide CDN.

So the first thing built is a throwaway HTML file, thirty lines or so,
that loads Pyodide, writes `src/anime_character_creator/` into its
filesystem, imports the package, calls `render_character(PRESETS["krista"])`
and puts the result in the document. Specifically worth confirming while
it runs: that `colorsys` is present in Pyodide's stdlib, that frozen
dataclasses behave, and that Pyodide's Python satisfies the
`requires-python = ">=3.11"` floor.

**Kill condition:** if that spike cannot import the package and draw one
preset, this plan is void and the rejected list above becomes the
shortlist. It would then be re-decided from scratch rather than taken in
the order written: the objection to Hugging Face Spaces is about what
hosting a no-image-models project on the model-demo site says, and that
objection does not weaken just because the preferred route failed.
Nothing else should be built until the spike draws Krista.

## The option surface as it stands

Today's parameters, counted:

| Where | Fields | What they are |
| --- | --- | --- |
| `CharacterParams` | 15 | colours, hairstyle, lengths, build, `outfit`, `face` |
| `Outfit` | 25 | one field per garment, mostly `str \| None` |
| `FaceStyle` | 14 | expression and eye geometry |

Fifty-four in total, plus five entries in `HAIRSTYLES` (`long_blunt`,
`short_layered`, `long_traced`, `short_crop`, `short_tousled`) and
fourteen presets.

Two facts about this pull in opposite directions, and resolving that
tension is the real design work in this project.

**The catalogue is already machine-discoverable.** `HAIRSTYLES` is a
real registry dict keyed by name. `Outfit` encodes garment presence as
"the colour is set", so garment slots and their colour controls can be
derived from `dataclasses.fields(Outfit)`. That means adding a hairstyle
or a garment in Python could make it appear in the web UI with no
JavaScript edit at all, which preserves the no-drift property from one
end to the other.

**But blanket introspection is the wrong tool.** Fourteen `FaceStyle`
floats including `eye_corner`, `eye_lower_lid` and `brow_weight` is a
mixing desk, not a limited set of choices, and it hands a non-technical
visitor an excellent chance of building something broken. It is the
opposite of what this page is for.

## The catalogue module

The resolution: a small new module in the package, say
`src/anime_character_creator/catalogue.py`, that names which parameters
are public, in which order, with which labels and ranges. It emits that
as JSON, and the JavaScript holds **zero** knowledge of the character
model: no field names, no hairstyle list, no colour defaults.

**That JSON is written at build time as well as read at runtime**, and
the distinction matters more than it looks. If the page could only learn
the catalogue by asking Pyodide, then nothing at all could be shown
until Pyodide finished booting, which would take away both the instant
first paint in step 2 and the graceful floor described above: a preset
gallery cannot list fourteen characters if the JavaScript does not know
their names. So the catalogue is emitted to a static file, committed
next to `ref-out/`'s SVGs, and the running page reuses the same emitter
once Python is up. One source, two consumers, and the no-drift property
survives intact.

Widening the tool is then a one-file Python edit inside the package,
next to the model it describes, rather than a JavaScript file that
quietly falls out of date.

This only earns its keep if the test suite guards it, and `CLAUDE.md`
requires the tooling green in the same change. A JavaScript UI
contributes nothing there, but the catalogue is ordinary Python and is
straightforwardly testable:

- every field name it exposes still exists on `CharacterParams`,
  `Outfit` or `FaceStyle`
- every hairstyle key it offers is in `HAIRSTYLES`
- every exposed range renders without raising, at both builds
- every preset it lists is in `PRESETS`
- the committed catalogue JSON matches what `catalogue.py` emits now,
  guarded the way `refresh-ref-out.sh --check` already guards the SVGs

That is the guard that stops the catalogue decaying into the
hand-maintained list it exists to avoid.

## Knobs that are traps

Not every parameter makes a good control, and three are known problems
before anything is built.

**`shaded` is a switch that turns a killed behaviour back on.**
`CharacterParams` still carries it, but `CLAUDE.md` records the owner's
2026-08-06 call that the garment shadow planes were dropped rather than
narrowed, taking shadow-tone area from 5.9% of the chibi's ink to 0.9%
and from 15.3% to 3.1% at the taller build. Exposing it as a toggle
would offer visitors a one-click route back to the look the project
deliberately abandoned. This is a sharper trap than the two below,
because it is a documented reversal rather than an unexamined range.
It stays out of the catalogue.

**`heads` is a slider over builds nobody has looked at.** It spans 2.4
to 6.0, and this project's entire method is iterate-by-looking. Only the
two named `BUILDS` have actually been judged. Expose the named builds as
a toggle, never a continuous slider.

Related: `refresh-ref-out.sh` records that the tall figures moved out of
the top level on 2026-08-08 because the owner's call was that they do
not work well enough to publish, and `presets.REALISTIC_REFS` is down to
Satoko and Satoshi. That ruling was about the README, and whether it
also governs the web tool is one of the open questions below.

**Length floats can be sliders that visibly do nothing.**
`harness/hem/pullback.py` documents that `_skirt_hem_y` blends the
requested length in by `sk.build`, which is 0.1 at chibi, so lengths as
far apart as 0.60 and 0.95 land within four pixels of each other. A
skirt-length slider at the chibi build would move and change nothing
visible, which a user reads as a broken control, not as a subtle effect.

The general rule the catalogue should carry: per-knob ranges that were
actually looked at, not the full domain of the type.

## Layout and deploy

**The site does not go in `docs/`.** GitHub Pages' classic mode can
serve `/docs` from the default branch, and `docs/` here holds 172KB of
working notes, including `gap-analysis.md` and this file. None of that
should become publicly served web content by accident. The site goes in
`web/`, and a GitHub Actions workflow deploys it.

**`ref-out/` already is the pre-render step.** It holds SVG and PNG for
every named character, `refresh-ref-out.sh` regenerates it, and
`--check` already fails when it is stale. The instant-first-paint assets
in step 2 above are those files, reused. Building a second pre-render
path would create a set of images that can disagree with the ones the
README shows, for no gain.

**Pyodide loads from jsDelivr, with a self-hosted copy as fallback.**
GitHub Pages has a soft bandwidth allowance around 100GB a month; a
self-hosted runtime would spend roughly 10MB of it per first-time
visitor. Serving the runtime from a public CDN moves that off the quota
entirely, and leaves this site as a few hundred KB of text and SVG.

**PNG export, if wanted, happens in the browser and not via cairo.**
Put the SVG in an `<img>`, `drawImage` it onto a canvas, `toBlob`,
download. Fonts inside an `<img>`-rendered SVG are unreliable, but
`character.py` emits no `<text>` elements at all, so single characters
are safe. `sheet.py` and `cover.py` do emit text, which is one reason
sheet export is not in scope here.

## Constraints this inherits

From `CLAUDE.md`, unchanged and worth restating because a web layer is
exactly where they could get quietly broken:

- No AI image generation, anywhere in the pipeline. The web tool draws
  the same explicit SVG shapes.
- No external art assets. Everything served is generated by this code.
- **The web layer learns no geometry.** No coordinate, no head-radius
  fraction and no colour derivation belongs in JavaScript. If the page
  needs to know something about a character, it asks Python.
- Shape changes still need a render and a look before they are done, and
  the tooling still has to be green in the same change.

## Defaults taken without asking

Stated here rather than raised as questions, because the alternatives
are worse and the cost of being wrong is small:

- **A character is a URL.** Encode the parameters into the address bar,
  so a made character is a link someone can send or bookmark. Costs
  almost nothing, needs no server, and is the only sharing mechanism
  available without one.
- **Deploy from `web/` via Actions**, for the reason given above.
- **jsDelivr with a self-hosted fallback**, for the reason given above.
- **No sheet or cover export.** Single characters only, at least at
  first, on the text-rendering ground above.

## Decisions, settled 2026-08-10

The four questions this document was written to ask, and the owner's
answers.

**1. Customisation goes to the middle tier.** Start from a base, change
colours, swap hairstyle, add and remove garment slots. `FaceStyle` stays
out for now. Revisitable later, in either direction.

**And the malformed-combination worry is explicitly waived.** The
owner's call: ugly or broken-looking combinations are the price of
customisability and are the visitor's responsibility. That retires the
cross-product contact sheet that was going to gate this, so no
combination needs to be reviewed before it ships. It also means the
catalogue is a list of what exists, not a curated list of what looks
good, which is a considerably simpler thing to build and to keep
honest.

**2. The realistic build does not ship.** Chibi only. The deferral from
2026-08-08 stands and this changes nothing about it. `heads` and
`BUILDS` stay out of the catalogue entirely, which also removes the
worst of the trap knobs above.

**3. Three kinds of starting point: the named cast, a neutral male base
and a neutral female base.** The cast is what demonstrates the
generator and is a marketing surface for the novels; the neutral bases
are where someone goes to make a character of their own. **The novels
get a link from the page.** They are a free webnovel, so the link costs
the visitor nothing and is the reason the cast is worth showing.

Two of these do not exist yet. `PRESETS` holds the fourteen named
characters and nothing else, so the neutral bases are new work in
`presets.py`, built the way any character is, per `CLAUDE.md`.

**4. PNG as well as SVG.** Both offered, generated in the browser off
one canvas step, with no cairo involved.

## Licensing

Settled 2026-08-10, other than the two placeholders marked in the draft
text at the end. Not legal advice, and worth a lawyer's eye before it
goes on a public page.

### The repository used to contradict itself, and now does not

`pyproject.toml` declared `license = "MIT"` while `LICENSE` held 201
lines of Apache License 2.0. Both could not be right, and no
output-licensing story stands on an ambiguity in the licence underneath
it.

**Resolved to MIT**, by replacing `LICENSE`. The metadata already said
MIT, so nothing else changed. Relicensing was clean: 65 commits, one
author, one email address, so there were no third-party contributors
whose consent would have been needed.

Apache 2.0 was the incumbent only because it was first in a default
list. What it adds over MIT is a patent grant with a retaliation
clause, a requirement in section 4(b) that derivative works carry
prominent notices stating which files were changed, and an explicit
statement that trademark rights are not granted. The first manages a
corporate risk that does not exist for code that computes SVG
coordinates. The second lands friction on exactly the people this plan
invites to fork. The third is close to a wash, since MIT's silence also
grants no trademark rights.

Against that, MIT is about 170 words and can be read in under a minute
by someone who is not a lawyer, which matters here because the terms sit
on a public page beside a plain-language request. Anyone who cloned the
repository under Apache keeps those rights permanently, which costs
nothing, both being permissive.

### Why the ask has to be a request rather than a term

The stated intent is: use the generated characters freely, please link
back to the tool or the repository, and please do not claim you drew
them by hand.

The first two are straightforward. The third runs into something
structural. MIT grants use of the software without restriction, and
here **the artistic expression in the output is the
code's expression**: an SVG path in a downloaded file is the literal
output of a function in `character.py`. That is what would give an
output-copyright claim its force, and it is also what makes the
permissive grant arguably swallow any restriction placed on the output.
Someone who forks the repository, which the plan deliberately invites
them to do, has an even stronger position.

The code has to stay forkable, because that is the promise this whole
design rests on. So the honest resolution is that **the attribution ask
is a request, not an enforceable term.** Saying so plainly is better
than dressing it up, and a stated norm that people follow is worth more
than a clause that would not survive being tested.

### What is not given away

The permissive licence covers the code. It does not hand over the
characters' **names and identities**, and it does not hand over the
fixed art committed in `ref-out/`. Those are material from the novels
and stand on their own footing.

**What it deliberately does not try to cover is output a visitor
generates starting from a named preset**, and that restraint is a
decision rather than an oversight. The tool ships the cast as starting
points and lets a visitor recolour, restyle the hair and change garment
slots. There is no defensible line at which a recoloured Krista with a
different haircut and a different tunic stops being Krista, and page
copy is the worst possible place to attempt a similarity threshold.
Anyone who has changed every control on offer reasonably believes they
made something of their own, and telling them otherwise would be the one
paragraph on the page that reads as a threat.

So the ask is scoped to the identity instead of to the pixels: please do
not present the result as being that character. That is the thing worth
protecting, it is the thing a reader can actually comply with, and it
sits in the same register as the other two asks rather than
contradicting the promise that none of this will be enforced.

### Metadata does the work a clause cannot

Someone claiming they hand-drew a character is trivially disproved if
the file itself says where it came from. That is a better mechanism
than any term, and it is nearly free.

**In the SVG**, a `<metadata>` block carrying the tool URL, the licence
statement, the novel link, and the parameter URL that reproduces the
character. Attribution and reproducibility turn out to be the same
feature, given that a character is already a URL.

**In the PNG**, a `tEXt` chunk. The canvas `toBlob` path will not write
one, so it has to be injected into the PNG bytes in JavaScript, which is
a bounded piece of work: locate the header, splice a chunk, compute its
CRC32. Worth doing rather than accepting the loss, since the PNG is what
a casual visitor actually saves and posts.

**One design call: this is a parameter on `render_character()`,
defaulting to off.** Default-on would rewrite all seventeen SVGs in
`ref-out/` and churn the comparison baseline that the smoke tests and
`refresh-ref-out.sh --check` depend on, for no benefit to anyone using
the library directly. The web tool turns it on.

### The wording, as it should appear on the page

A draft, to be read as page copy rather than as a licence. The novel is
*The Hero of the Mist Tragedy*, published at
`https://www.honeyfeed.fm/novels/32712`, filled in below. Its source
lives at `../valley_of_mist/tragic_hero`, a private sister repo; the
published text is the "tragic hero" fork rather than that repo's main
branch, which matters only if this document is ever asked to link to
source rather than to the published read.

> **What you can do with what you make here**
>
> The code that draws these characters is open source under the MIT
> licence, and what you make with it is yours. Use it wherever you like,
> including commercially. No permission needed, no fee, no need to ask.
>
> Two things asked rather than required.
>
> Please link back, to this page or to the code, wherever a character
> ends up.
>
> Please do not present these as hand-drawn. A program drew them, and
> saying so costs you nothing.
>
> Neither is a legal condition. There is nothing here anyone intends to
> enforce.
>
> **One more ask, about the cast.** Satoshi, Krista and the rest are
> characters from *The Hero of the Mist Tragedy*. Start from any of
> them and change whatever you like; what comes out is yours the same
> as anything else here. The ask is only that you not present the
> result as being that character. The names, and who they are, belong
> to the story.
>
> The novel is free to read at
> *https://www.honeyfeed.fm/novels/32712*.

Three notes on why it is worded that way. It says what a visitor *can*
do first, because that is what they came to find out. It labels the two
asks as asks and then states outright that nothing will be enforced,
which is more credible than a vaguer form of words and matches the
owner's position exactly.

And the cast paragraph is about names rather than about pixels, for the
reason given above. An earlier draft of this said the cast's designs
stayed with the author and pointed people at the neutral bases for
anything they wanted to own. That collided with the tool's own design:
it hands visitors the cast as starting points, lets them change every
control on offer, and then would have told them the result was not
theirs. Scoping the ask to the identity keeps the paragraph in the same
register as the two above it, and asks for the only thing that was
actually worth asking for.

## What has to be built

In order, with the first item genuinely first.

1. **Done, 2026-08-10.** The Pyodide spike. Krista imported and rendered
   in a real browser off the unmodified package; the kill condition
   never fired.
2. **Done.** Two neutral base presets, `BASE_FEMALE` and `BASE_MALE` in
   `presets.py`, exposed as `NEUTRAL_BASES` and kept out of `PRESETS` for
   the reason given where they're defined.
3. **Done.** `catalogue.py`, `refresh-catalogue.sh` as its build-time
   emitter (`ref-out/catalogue.json`, committed the way the SVGs are),
   and the pytest guards in `tests/test_catalogue.py`.
4. **Done.** The `metadata` parameter on `render_character()`, off by
   default; `attribution.py` builds the block, `urlstate.py` is the
   encode/decode a link and the metadata's own reproduction link both
   share.
5. **Done.** The page in `web/`, staged flat by `web-stage.sh` (index.html
   plus `ref-out/` and `src/anime_character_creator/` as siblings, which
   is what the page's relative fetches need), the Actions deploy at
   `.github/workflows/pages.yml`, and PNG export (canvas, then a spliced
   `tEXt` chunk for attribution) alongside the URL-encoded share link.
   Tested end to end in a real Chrome tab: gallery paints before Pyodide
   is up, every preset and both bases render and edit live, downloads
   carry working metadata, and a malformed `?c=` link fails to the
   gallery rather than to a broken page.

The licence work that used to head this list is done; the licensing
section above is its record.

**Left undone, deliberately.** The self-hosted Pyodide fallback this
document names as a mitigation for a blocked CDN: it means vendoring the
whole Pyodide asset bundle, tens of megabytes, and nothing here has
measured whether that CDN block is a real problem for this audience
rather than a hedge. jsDelivr only, for now.

**Left for the owner.** GitHub Pages does not turn on by pushing code:
Settings → Pages → Build and deployment → Source has to be set to "GitHub
Actions" once, by hand, in the repository's own web UI. Nothing above can
do that step.
