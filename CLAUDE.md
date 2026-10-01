# Aspire Health — static site, built by one Python script

## Team: who works where, and who pushes

RAW 0: EM is Peter's main thread for this site. It takes requests, runs helper agents in parallel —
each in its own worktree — and does all merging, pushing and publishing. Other sessions each keep
their own git worktree and branch:

| Session | Folder | Branch | Status |
|---|---|---|---|
| RAW 0: EM | `~/Desktop/Raw` | `main` — the live site | main thread |
| RAW 3: Logos | `~/Desktop/Raw-worktrees/logo` | `logo/design` | active: logo direction |
| RAW 1: General | `~/Desktop/Raw-worktrees/raw` | `raw/work` | parked; its work is in `main` |
| RAW 2: Backgrounds | `~/Desktop/Raw-worktrees/raw2-fizz` | `prototype/fizz-and-wipe` | parked; fizz-and-wipe prototype kept on its branch |

A parked session starts no new work unless Peter restarts it.

Every session except RAW 0: EM:
- Works only in its own worktree and commits only to its own branch. Commit as often as you like.
- **Never pushes.** `main` deploys straight to the live site on GitHub Pages, so only RAW 0: EM pushes,
  and only after Peter says go.
- Never publishes the private preview artifact (claude.ai/artifact/KgFJMrNRkPX2ukMEsSQ8Ek). RAW 0: EM
  publishes it. Every publish includes `style.css` or the pages ship unstyled, and the 300 pour frames
  exceed the 255-file limit per publish, so they go up in a second call.
- Never checks out, commits to, or merges into `main`.
- To pick up what has shipped, merges `main` into its own branch.
- Messages RAW 0: EM when a piece is ready. It merges it into `main`, rebuilds, checks it and reports.

A new session gets its worktree from RAW 0: EM: `Raw-worktrees/rawN-<topic>` on branch `rawN/<topic>`.

**The first build in a fresh worktree takes ~50s**: checkout leaves the cut photos no newer than
their sources, so every photo is re-cut. The output is byte-identical and git sees no change. Later
builds are ~0.05s again.

## Merging: never merge the generated pages

`.gitattributes` marks `homepage.html`, `category-*.html`, `about.html` and the root `style.css` as `merge=ours`, so
two branches that both rebuilt never conflict on them. A post-merge hook then rebuilds them from the
merged source; commit what it rebuilt. The `ours` driver is local git config
(`git config merge.ours.driver true`) — set it in any fresh clone, or git falls back to a normal
merge and those files conflict. If a merge stops on a conflict in *source*, the hook does not run:
resolve the source, run the build, then commit.

## Never read the generated pages

`homepage.html` is ~310k chars (~78k tokens). All ten generated pages together are ~1.81M
chars (~453k tokens). All ten files in `site-src/` together are ~415k chars (~104k tokens).
(Measured 2026-09-27 on the bar theme with 101 products and nine shelves; there are 105 products
and ten shelves now, so there are eleven generated pages and every figure above is low. The pages
grow with the script, the icon sprite and the product count, so re-measure rather than trusting these.)

**One generated page costs as much as three-quarters of the entire source, and the ten
together cost four times the source** — and every line of them is a copy of something
the source already says better. To check something in a generated page, grep it:

    grep -n "pod-count" homepage.html | head
    grep -c "card-link" category-protein.html

Never `Read` a generated `.html`. If you want to know why the output looks a certain way, read
the source that produced it — the template, `style.css`, `_script.html`, or `build_homepage.py`.

## Source vs. generated

Source (edit these):
- `site-src/build_homepage.py` — all layout logic, plus the `FAMILIES`, `CATEGORIES`,
  `FEATURED`, `GOAL_TILES`, `ISLANDS`, `CAROUSELS` tables
- `site-src/homepage.template.html`, `site-src/category.template.html`, `site-src/about.template.html`
- `site-src/_header.html`, `_footer.html`, `_dialogs.html`, `_icons.html`, `_script.html`, `_intro.html`
- `site-src/mark-glow.svg` — the lit wave the opening curtain arrives on. JSON-encoded into the
  script as `{{GLOW_SVG}}`, so it never reaches the markup and a no-JS visitor is served none of it
- `site-src/style.css` — copied to `style.css` at the repo root at build time; every page links it via
  `{{STYLE}}`, which the build fills in with a content-hash query string. It sits at the root, not under
  `assets/`, so its `url(assets/...)` backgrounds keep resolving against the page's own folder
- `share-links.csv` (`product,share_link,photo`) — the product list, 105 rows
- `bestsellers.csv` (`product,units_this_week`) — top 3 rows become the podium; `product` must
  match a `share-links.csv` name or the build exits. Blank `units_this_week` just hides the count.

Generated (never hand-edit; the next build overwrites them):
- `homepage.html`
- `about.html` — the About us page, from `site-src/about.template.html`: their two portraits, who they
  are (`peter_text`, and the same `her_text` block the Women's Health shelf carries), the proof wall
  (`proof_wall`: his three pairs and her two), both DEXA cards, then the free sample and the call with
  the Amway disclosure. It is where the menu's "About us" goes, from every page. The proof used to
  close the homepage's story; Peter moved it here (2026-09-28: it "feels like too much in one thing"),
  and the story's ask carries one link across to this page. One "Who we are" title sits over the pair, with
  "Peter" and "Yenni" as the headings, so `her_text` takes `label=None` and a `title`. Both speak in the
  first person: his lead is PETER-COPY, and Peter asked on 2026-10-01 for hers to be first person too
  (`her_text`, shared with the Women's Health shelf; it stays DRAFT until Yenni has read it). His four "What
  changed" bullets were rebuilt from his own story lines and Peter approved them (PETER-COPY, 2026-10-01).
  His proof-wall pairs are labelled "Month 1 → Month 15" (`PETER_PHOTOS`) in the slot where Yenni's
  "Nov 2025 → Jul 2026" sits, and the story's tags read "Before · Month 1" / "After · Month 15": months of
  his fifteen, never calendar dates, which is his choice. His caption "Fifteen-month transformation." stays. From 760px the hero is as tall as its portraits; from 1220px the two DEXA
  cards are one height with their heads aligned (his four numbers one per row), and between 1000 and 1219px
  they stack. The closing block is centred. Generated, never hand-edited.
- `category-daily-foundations.html`, `-energy-focus.html`, `-everyday-health.html`, `-fat-loss.html`,
  `-hydration.html`, `-protein.html`, `-recovery.html`, `-skin-redefined.html`, `-womens-health.html`,
  `-mens-health.html` — ten shelves. Everyday Health (2026-10-01) is the tenth: Cholesterol Health,
  Liver Support, Heart Health CoQ10 and Cellular Aging Support, the four that fitted none of the other
  nine. Its plate is a satin garnet, #80222F, at rank 9 (it was petrol #2B4E58 until 2026-10-01, which on
  the barbell and in the "Your stack" key read as the same dark mark as Men's green; the PLATES comment has
  the measurements). The rack is two a row on a phone (five even rows), three and a lone tenth from 768 to
  1023, and two rows of five from 1024; the pinned bar carries ten at 320 with room for about four more
  before its shaft hits the minimum. Its copy is count and dose off each pack's own label and never what it
  does (CoQ10 is the one ingredient named, the only one printed legibly on any of the four); its plate line is
  "Day in, day out". Its banner is described below. Nothing on it carries fact chips, because amway.com is
  blocked to us. The Protein shelf was "Protein Snack Pack" until 2026-10-01; Peter approved "Protein".
  On every shelf page "Keep looking" is rows on a phone and a tile grid from 768 (two across, three from 1024).
- `style.css`, `assets/products/`, `assets/cutouts/`, `assets/.cut-version`

`docs/macro-calculator.md` records the homepage macro calculator: where the maths came from, every
formula and rounding in `mcCalc` in `_script.html`, and worked examples. Read it before touching them.

**There are no preview pages right now.** The bar theme they previewed is the live site (2026-09-28),
so `homepage-demo*.html`, `category-*-demo-bar.html` and their stylesheets were deleted at Peter's
request. The build still has the export that made them: `python3 site-src/build_homepage.py --demo OUTDIR
[--demo-name NAME]` writes `homepage-demo[-NAME].html`, a `category-<slug>-demo[-NAME].html` for every
shelf and `style-demo[-NAME].css`, all `noindex`, with every internal link rewritten to the demo copies
and their own stylesheet, so a preview can never change the live pages. RAW 0: EM copies them in and
pushes. A preview's sample form really sends (FormSubmit), so only publish one Peter has asked for.

**"Take my stack to Amway" (`#sa`).** The step from a loaded bar to a real order, added 2026-10-01 off
Peter's own finding that Amway attribution is session-wide: one click on a share link credits him for
everything added afterwards, including items the visitor finds by ordinary browsing. The button lives
inside `.mys-has` under "Build yours." on the homepage only, and shows only when at least one plate is
loaded and `<dialog>` is supported; the modal shell comes from `stack_dialog()` in the build and is
filled by `_script.html`. There is no add-to-cart-by-URL at Amway (the only addresses are product and
category pages), so the panel is: pick (every product ticked, untick to drop) → `window.open` the first
one through its share link → a checklist of the rest, where each "Add" opens that product's share link on
Amway in a new tab and ticks its row (a tick can still come off by hand; "Open again" on the first row never
unticks). They cannot share one named tab: measured in Chrome 2026-10-01, a named target reaches a tab only
if it was opened without noopener, and the first opens with noopener on purpose — so the copy says each
opens a new tab. The panel scrolls to its top on every phase change, so its new lead is what shows. The
credit line says Amway credits the order to Peter, the buyer pays Amway's normal price (Peter confirmed),
and there is no code to enter. The rack points to it twice once a plate is loaded: the rack guide's step 3
(Peter's wording: "Add to cart, bring it to a free call, or ask for a sample."; "Add to cart" is `.rg-amway`, which is plain text, an `<a>` with no href, until a plate is loaded:
`amwaySync()` gives it its href on the same state that shows `.rk-amway`) and a slim `.rk-amway` button in each open bay; both work `#sa-go`,
through `toAmway()` in the rack block. The product card's own button reads "Buy on Amway", never "Add to
cart": it opens the product's page. The products offered
are read back out of the rack's own panels (`#rk-p-<slug> .bay-go`, href moved to `data-href` by the
product-card block), never a second table in Python — so a new shelf needs nothing here and the links can
never drift from `share-links.csv`. `sessionStorage` holds `aspire-amway-done` (the ticks) and
`aspire-amway-run` (`{off, first}`: the picks left out and the one opened first), so a reopened checklist is
the one the visitor started.

`index.html` is a hand-written redirect to `homepage.html` and is not generated.

`assets/bg-everyday-health.webp` is the Everyday Health shelf's hero banner, and the only one of the ten
that was generated rather than shot or licensed: fal-ai/flux-pro/v1.1-ultra, 2026-10-01, from
`~/Desktop/aspiree/tools/jobs-everyday-banner3.json` (three passes; passes 1 and 2 missed the house look and
their prompts say how). It is four clear glass columns in an even row on sand against a deep petrol wall —
the same still-life language as the seven shot banners, and what the shelf means. Its petrol wall no longer
matches the shelf's plate (now garnet). A Fable critic scored it 3/10 (2026-10-01: centred, all in focus, no
dispersion, and its pale horizon runs through the shelf name on a phone); Peter has parked it, so leave it
until he asks. It carries no product, no
pack and no lettering, so nothing in it can read as a claim. It is centre-cropped to 16:9 and resized once to
1600x900, WebP q78; the frame it came from is kept at
`~/Desktop/aspiree/assets/generated/raw-site/everyday-banner-v3-1.jpg`. It is placed by hand, so the build
never rewrites it, and a real photograph drops in by overwriting this one file.

`assets/wave-horizon.webp` is the footer's horizon: Peter's lit wave, cropped to the wave band
alone (his artwork carries the lockup type under it, which must never reach the page). It is
placed by hand, not generated, so the build never rewrites it and nothing cleans it up.

`assets/peter/` holds Peter's photos for the story and the proof wall: `family-320.webp` (Peter, his
wife and daughter), his before/after composites `front-`, `side-`, `back-` at `640.webp` and `960.webp`,
and `side-before-480.webp` / `side-after-480.webp`, the two halves of the side pair cut at its
seam (crop only, WebP q92) for the story's opening before and its before-becomes-after wipe.
They are cut from his originals in `~/Desktop/aspiree/assets/rooms/` and placed by hand, so the
build never touches them. `with-daughter-640.webp` / `-960.webp` (640x800 and 960x1200, 4:5, WebP
q90) are his portrait holding their baby daughter at an evening event, the Men's Health hero and the
pair to Yenni's. They are cut from Peter's own photo (a 1179x1576 screenshot, Display P3): one crop,
x 0-1080 and y 226-1576, clear of the screenshot's black band on rows 0-6, with his hair ~9% below
the top and the baby's feet whole; converted P3 to sRGB so the colours hold once the profile is
gone; then a uniform Lanczos resize. No retouching, no exposure or white-balance change, and no
metadata: each file is a bare VP8 chunk (no EXIF, XMP or ICC). Peter chose to make them public; the repo is public because Pages
requires it. `hero-pair-160.webp` / `hero-pair-320.webp` are the homepage hero's portrait (`.hero-me`): Peter holding their
daughter, both faces whole, which is how he wants it (2026-10-01: "it also doesn't include my daughter, which I want
it to"). They are the box (205,78)-(675,548) of `with-daughter-960.webp`, one Lanczos resize, q90, bare VP8, drawn
as a 14px-radius rounded square (a circle would clip her bow and his hair). They sit beside the PETER-COPY line
"I'm Peter — husband, dad to a baby girl, and a Lincoln local.", the DRAFT "My story" link and the plan's two links:
`.hero-actions` lives inside `.hero-me`, so the button shares the picture's height instead of adding to it. The block
lays itself out by the copy's own width (container query on `.hero-copy`); under 300px the links take a full row
below. The picture is 126px at 390, 140px at 1440. On phones the hero label is hidden, the headline is 15vw and the
copy's top padding is 8, so "See the game plan" ends at 830 of 844 (390x844) and 808 of 812 (375x812): any added
height above it pushes it off the first screen.

**What may be edited, and what may not.** Crop, exposure and white balance are always fine. Peter
has also allowed extending BACKGROUND at the edges when framing needs it (2026-09-25) — plain wall
or door panel only, never across an object and never near his outline. **His body is evidence and
is never retouched, smoothed, slimmed or reshaped.** As shipped, nothing is synthesised: all six
halves are straight crops. The one exception is the back BEFORE half, which carries a half-strength
row-wise horizontal rescale that Peter chose to straighten the room's converging door frames; it
widens his waistband ~4.9%, which makes the transformation read slightly larger than it was. Never
increase that without asking him. The three pairs share one framing spec measured on his body, and
the seam must stay at exactly 50% with befores on the left, or the page's Before/After headings
stop aligning.

`assets/her/` holds the photos of Yenni, Peter's wife, who runs the women's side of the business.
Peter approved her name, photos and results going public (2026-09-27). The site calls her "Yenni",
which is `HER_NAME` in `build_homepage.py`; never use the longer name on her scan reports. These are
the files:
- `front-640.webp` / `front-768.webp` and `back-640.webp` / `back-768.webp`: her before/after pairs,
  with the before on the left and the after on the right, 640x816 and 768x979.
- `front-before-384`, `front-after-384`, `back-before-384`, `back-after-384`: the four halves on
  their own, 384x979, framed the same way. No page uses them yet.
- `with-daughter-640.webp` / `-960.webp`: her portrait with their daughter, 4:5, the Women's Health
  hero.

The pairs are cut from one composite of four panels: the before front and back from Nov 2025, and the
after front and back from Jul 2026. It was split at its white panel seams, so the dividers and their
anti-aliased columns are left out. All four halves share one framing spec measured on her body. Let L
be the distance from her crown (the top of her head's hair line, not the ponytail) to her knee (the
kneecap centre from the front, the knee crease from the back). The frame runs from 6.5% of L above the
crown to 4.5% of L below the knee, and it is centred on her midline between the knees. The measured
landmarks are:

| half | crown y | knee y | midline x |
|---|---|---|---|
| before front | 82 | 890 | 207 |
| before back | 88 | 949 | 576 |
| after front | 82 | 866 | 976 |
| after back | 73 | 881 | 1330 |

These are composite pixels. Each half is scaled uniformly (the same factor in both directions) so
that every L comes out the same size. The seam sits at exactly 50%. The before-front crop starts
at x=31: that removes the wall charger and its cable at the bottom left and stays 3px clear of her
hand.

The portrait is the box (165,300)-(1197,1590) of her photo, clear of the screenshot's black bars.

The editing rules match Peter's. Crop, exposure and white balance are allowed, and so is extending
plain background at the edges, but never across an object or near her outline. **Her body is evidence
and is never retouched, smoothed, slimmed or reshaped.** As shipped, every file is a crop plus a uniform
resize. Nothing is synthesised, no colour was touched and no background was extended. Every file is
rebuilt from raw pixels, so it carries no EXIF, XMP or ICC data: each is a bare `VP8 ` chunk. The files
are cut from the originals Peter sent and placed by hand, so the build never touches them.

Her photos have their own dates (`HER_PHOTOS`: Nov 2025 → Jul 2026), about two months and ten months
after their daughter's birth in Sep 2025. They are never presented as matching her DEXA scans.

**The DEXA cards.** Peter's card (`peter_card()`, from `PETER_TRANSFORM`) shows the two scans of his
transformation, fifteen months apart: body fat, weight, and pounds of fat and of lean. No dates, no trend, no
clinic — that is Peter's choice (2026-09-28), and his later UC Davis scans are deliberately not used anywhere.
**Every one of the four rows is read off his reports** (2026-09-28: he relayed the figures rather than uploading
the scans), so nothing on the card is derived and the card carries no worked-it-out line. `PETER_TRANSFORM` holds
them as (weight lb, body fat %, fat lb, lean lb) before and after. The rows do not sum to the weight and must not
be made to: a DEXA total also carries bone mineral. `PETER_SHOW_COMPOSITION = False` takes the fat and lean rows
off every page in one edit. Yenni's card shows fat and lean as her scans
measured them, and is not affected. `HER_DEXA` holds Yenni's scans as data
rows: date, weight, fat, lean and body fat %, from UC Davis Sports Medicine in Sacramento. `dexa_card()` draws
her card, with these parts:
- The headline, which compares the first scan with the last.
- A trend of fat mass and a trend of lean mass, each on its own zero-based axis with a time-true x.
- A visually hidden table of every scan.
- The source line and the disclaimers (`DEXA_NOTES`).

Weight is stored but never shown. Nothing else from the reports is used: no logo, layout or colours,
and no date of birth, patient ID or height. Her scans have a gap (`'gap'`) from Dec 2024 to Aug 2026,
which spans her pregnancy and their daughter's birth. Her trend is drawn broken there, with no line
across the gap, and the card says why. Set `HER_DEXA = None` and her card comes off every page.

Where it all shows:
- `about.html`: the proof wall — her pairs beside Peter's — then both cards. It used to close the
  homepage's story; Peter moved it to About on 2026-09-28.
- Women's Health: her portrait as the hero, drawn as a real `<img>` (`SHELF_PORTRAIT`), then her
  story, pairs and card (`SHELF_EXTRA`).
- Men's Health: Peter's card (`SHELF_EXTRA`).

`assets/story/` holds AI-relit shots of all five story products (whey, GI Primer, XS Creatine+, XS
Elite, Sleep Health, as `*-lit.webp`): relit with fal-ai/flux-pro/kontext, cut out with
fal-ai/birefnet/v2, and placed by hand, so the build never touches them. Each was checked so that the
name, logos, colours and shape match the real pack, while fine print may differ. The GI Primer shot
is ~7% taller than the real tub (Peter accepted it). On the whey the model got lines wrong (net
weight, servings, the caption under FREE), so those were softened to illegible rather than left
stating a wrong number. XS Elite was regenerated for realism from the real catalogue can (droplets,
metallic rim): its volume line reads the true "12 fl oz (355 mL)", and because kontext widened the
can on every try, the cut-out was squeezed horizontally back to the real can's proportion — an even
rescale, nothing redrawn. The sleep bottle's base rim had the lit set's teal
bounce white-balanced out. Each file is framed like the catalogue image it replaces (same centre x,
baseline and pack area; the whey measured on the pouch, with its scoop in front), so the story's
`data-*` attributes and `.st-shade` carry over unchanged. Only the story uses them; the product cards,
shelf pages and podium still use the catalogue images.

## The story (`#story`)

The homepage runs hero → `#how` (the five-step game plan) → `#goals` (the plate rack) → `#sample` →
`#macros` → `#trending` (the week's three best sellers, each with its TAGLINES line, all three in view at
every width; the scroll-scrubbed can pour behind them is `TRENDING_POUR`, off) → `#story` → `#my-stack`
→ `#consult`. The calculator moved up beside the free sample on 2026-10-01 (the game plan offers it as the
alternative: "or run your macros first"); Peter had moved it below the story on 2026-09-26 because it "came
too early" straight after the shelves; shown it again with the critic's score for it there (9/10), he chose
to keep it beside the sample (2026-10-01). Because the consult no longer follows it, the
automatic glide after "See my numbers" only runs when `#consult` directly follows the calculator's section;
the result card's own "Book a free call" carries the numbers into the form. `#story` is a sticky, scroll-scrubbed stage telling Peter's 15 months in
beats, in three movements ("Fatigue was a constant." / "Here's what I changed." / "Here's what I
notice now.", his own phrases for them): his before, one growing shelf with three product beats and a
fourth that lands the last two packs together, then the before becoming the after and his family,
"That's what this call is for" with a "Book a free call" button and, under it, the one link across to
`about.html` ("See Yenni's results and both our DEXA scans", DRAFT, `.st-more` inside the ask beat), which
carries the proof wall and the DEXA cards. Nothing sits between `#st-run` and `#my-stack`. The pinned strip
is Peter's only while `#st-run` crosses the strip's foot AND still reaches the window's foot (two one-pixel
IntersectionObserver lines in `line()`): the moment the run ends and "That's my stack" starts coming up, it
hands back to the visitor's own stack, or steps aside if they have none.
The wall is not on the homepage any more (Peter, 2026-09-28: it "feels like too much in one thing"), and
the menu's "About us" is the way to it from anywhere and from any shelf page — the site is not getting a
third fixed layer for it. The story replaced the old `#hydrate` band (its water line now lives in the
hydration beat).
A visible heading opens the section — PETER'S STORY over "How did I get into this?" (`.st-head`),
his own words for it. It sits outside `#st-run`, so it scrolls away normally and the run is no longer for it.
Peter's lines inside it are his, verbatim, in PETER-COPY markers.

**His words are a caption strip, not one line at a time.** Under whatever the stage is showing,
`.st-caprail` holds his six lines in one column and the script slides its track so the caption belonging to the pack on the
stage sits on the reading line at full strength, with the ones above and below in a softer teal
(5.3-5.9:1 on the ground: quiet, never unreadable); two or three are legible at once (Peter,
2026-09-28: "it needs to be a lot easier to read... maybe I can read it in one go"). A caption belongs to the beat
carrying `data-cap`, in order (his before, the four packs, the turn); his family beat has none,
because the third movement's line is already up when it arrives. Two of the captions open a movement
with a small `.st-mv` label in his words. All of them are his verbatim except one DRAFT-COPY line,
the one that folds the old morning-routine and smoother-energy beats into one and still links Daily
Foundations and Energy & Focus. The strip sits over the beats (`z-index`), so its links can be
tapped, and the script gives it `.is-off` once it has faded so the ask's own button takes the tap.
Its edges fade over `--cap-fade` (about one and a half caption lines; 72px at desktop, registered with
`@property` so the script can read it), and the script also writes each caption's own opacity per frame, so a
line recedes rather than being sliced at the strip's edge. The strip fades in as the stage arrives, so the
first pinned screen carries "Fatigue was a constant." with his before photo. At desktop it starts below the
pinned bar, the before/after and family photos fill the stage height (up to 760px, never more than half the
stage's width; 528x704 at 1440x900, 16px clear of the pinned bar and the screen's foot), and the ask is set in the
captions' display type, centred. On phones the photo sizes are measured: `measure()` sets `--st-ph` (the before and the
wipe, always one size) and `--st-fh` (the family, never past its own 320x400) once per resize, so the photos grow down
into the empty top of the caption strip and stop 18px above the line their caption reads on (306x408 at 390x844, up
from 236x315; Peter, 2026-10-01: "the picture is too small"). While a photo is up, an earlier caption fades as it
rises past the photo's foot. The mat is 10px on phones, 14px from 768.
`family-320.webp` is only 320x400, so at desktop it is enlarged and soft; a sharper cut would come from
Peter's originals.
Without the stage it is a plain block of his six lines with their links, straight after his before,
so a no-JS reader gets the whole story in his words and then the pictures it is about.
Each pack carries `data-cat`, the shelf whose plate it puts on the pinned bar, so one beat can load
two plates; the build checks those against `PETER`, which is in the story's order (protein,
hydration, recovery, daily-foundations, energy-focus). His five plates load 1, 2, 3, then 4 and 5 a
slide apart under the closing line, so the bar still reaches PETER'S · 5 OF 5.
The five packs all rest at `data-tilt="0"`: they stand straight in the group that gathers on stage,
and the only turn left is the fall's own lean (`DROP.lean`), which unwinds to nothing at the landing.

Its pace lives in the story block of `_script.html`: the `HOLD` table and the per-change lengths. A unit is
`UNIT=.33` of the stage (~278px at 844), and the script sets `#st-run`'s height in px on every resize; the
350lvh in `style.css` is only the fallback until it measures. `HOLD` is
`[.45, .25, .25, .25, .25, .85, .3, <measured>]` with `TT` (the change INTO each beat)
`[0, .6, .45, .45, .45, .6, .45, .9]`: his before, the four pack beats, the turn, his family, the
ask. Every hold but two is short, because nothing waits for a line to be read — the strip is already
showing it — and a hold is only the moment a picture stands on its own. The two long ones are the
turn (.85, the wipe plays inside it) and the ask, whose hold is measured per resize: the hold plus the
button's own way off the screen equals `FLICK` (780px), never less than `CALLMIN` (.8 units). That is ~316px
at 390x844 (run 2976px) and 246px at 1440x900 (run 3082px), and it is what makes every 700px flick that enters
the ask come to rest with "Book a free call" whole on screen (re-measured on merged main 2026-10-01: a window of
800px at 390x844 and 820px at 1440x900 after the bigger photos, 30/30 flicks each). Changing any of these means re-running the
flick test before shipping. The stage renders from an eased copy of the scroll position with
a speed cap and a backlog clamp, so a fast flick still plays each fall; it is still a pure function
of scroll, so scrolling back plays it backwards. Transforms and opacity only (a full scrub costs 0
layouts); keep it that way. Reduced motion and no JavaScript get the same beats as a plain vertical
sequence. It was tuned over four Fable review rounds; the rounds are tagged `story-round-0` to
`story-round-3`, and `PRE-STORYBOARD` is the site before it.

**The rack (`#goals`).** Tapping a plate opens its bay directly under that plate's ROW: `.rack` is the flex
container, `.rk-plates` is `display:contents` with `role="list"`, and `place()` in the rack block sets only
`order` (the open panel 1, the plates after its row 2), reading the row length from `--cols`. There is one copy
of each panel, so ids and aria stay single and Tab still goes plate → its panel. A notch on the panel's top edge
points at the plate. `show()` brings the plate and its packs into view together when they fit, otherwise the
whole panel (Peter, 2026-09-28: tapping a plate must show "where the items actually are").

**The rest of the homepage.** The bottom tab (`.mtab`) is phones and tablets only: hidden whole from 1024 up,
where the header nav already carries MACROS. The quick-call card that sat under the sample form is gone;
`#quick-call` now marks the consult's `.wrap.split` until a sample is sent, when the script hands the id to the
thank-you's call invitation, so the game plan's step 05 link still lands. From 768 the sample section's text is centred vertically against its card. The sample form's shelf picker uses
container queries so the ten sit evenly (two a row on phones, five on the desktop card). From 1024 the booking
card fits 1440x900 under the masthead (745px, 797 with the summary showing) with every question and option
unchanged: re-measure if one is added or reworded.

A product can sit on more than one shelf: a shelf page lists everything its own `CATEGORIES` entry
names, while `cat_of` stays each product's single home shelf (its card tag). XS Creatine+ is on both
Daily Foundations and Hydration; the Women's Pack and the women's multivitamin tablets and gummies are
on both Daily Foundations and Women's Health (their home shelf, being later in `CATEGORIES`), and the
men's likewise on Daily Foundations and Men's Health.

Women's Health's hero is Yenni's portrait with their daughter, from `assets/her/`, shown whole as a real
`<img>` beside the name (`SHELF_PORTRAIT`). The old placeholder, `assets/bg-womens-health.webp` (the Women's
Pack on a plum field), is still there but no page shows it. Men's Health's hero is its pair: Peter's portrait
with their daughter, from `assets/peter/with-daughter-*.webp`, through the same `SHELF_PORTRAIT`. Its old
placeholder, `assets/bg-mens-health.webp` (the Men's Pack on a green field), is likewise kept but unused. A product with no
fitting shelf stays out of `share-links.csv` altogether: the homepage grid, search and the sample
form list every row, so a row on no shelf still shows up there, tagged "Wellness".

## Build

    python3 site-src/build_homepage.py     # from the repo root

Takes ~0.05s and prints `105 products (105 with photos)` plus the per-category counts. Run it after
any source edit; nothing else regenerates the pages.

## Why a build sometimes takes ~50s instead of 0.05s

`normalize()` cuts each photo in `product-photos/` into `assets/products/` (and, for the podium,
`assets/cutouts/`). It is cached two ways: a photo is skipped when its output is newer than the
source, and `assets/.cut-version` holds a sha1 of `normalize()`'s own source text. **Editing the
body of `normalize()` changes that fingerprint and forces a full re-cut of every photo — ~50s.**
That is expected, not a hang. Deleting `assets/.cut-version` does the same.

`product-shots/<slug>.webp` (already-lit studio shots, 15 of them) wins over `product-photos/` and
is copied straight through without any cutting.

## Absolute URLs

Everything on the site is linked relatively, because it is served from a subpath
(`3p3t3.github.io/RAW/`), not a domain root. The only exception is Open Graph and Twitter
cards, which scrapers require to be absolute: those come from `BASE` in
`site-src/build_homepage.py`, substituted as `{{BASE}}` and `{{PAGE_URL}}`. Moving to a
custom domain means editing `BASE` and nothing else. `site.webmanifest` uses `start_url: "."`
for the same reason — `"/"` would point at the wrong site.
