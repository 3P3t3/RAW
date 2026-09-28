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

`.gitattributes` marks `homepage.html`, `category-*.html` and the root `style.css` as `merge=ours`, so
two branches that both rebuilt never conflict on them. A post-merge hook then rebuilds them from the
merged source; commit what it rebuilt. The `ours` driver is local git config
(`git config merge.ours.driver true`) — set it in any fresh clone, or git falls back to a normal
merge and those files conflict. If a merge stops on a conflict in *source*, the hook does not run:
resolve the source, run the build, then commit.

## Never read the generated pages

`homepage.html` is ~310k chars (~78k tokens). All ten generated pages together are ~1.81M
chars (~453k tokens). All ten files in `site-src/` together are ~415k chars (~104k tokens).
(Measured 2026-09-27 on the bar theme with 101 products and nine shelves; the pages grow with
the script, the icon sprite and the product count, so re-measure rather than trusting these.)

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
- `site-src/homepage.template.html`, `site-src/category.template.html`
- `site-src/_header.html`, `_footer.html`, `_dialogs.html`, `_icons.html`, `_script.html`, `_intro.html`
- `site-src/mark-glow.svg` — the lit wave the opening curtain arrives on. JSON-encoded into the
  script as `{{GLOW_SVG}}`, so it never reaches the markup and a no-JS visitor is served none of it
- `site-src/style.css` — copied to `style.css` at the repo root at build time; every page links it via
  `{{STYLE}}`, which the build fills in with a content-hash query string. It sits at the root, not under
  `assets/`, so its `url(assets/...)` backgrounds keep resolving against the page's own folder
- `share-links.csv` (`product,share_link,photo`) — the product list, 101 rows
- `bestsellers.csv` (`product,units_this_week`) — top 3 rows become the podium; `product` must
  match a `share-links.csv` name or the build exits. Blank `units_this_week` just hides the count.

Generated (never hand-edit; the next build overwrites them):
- `homepage.html`
- `category-daily-foundations.html`, `-energy-focus.html`, `-fat-loss.html`, `-hydration.html`,
  `-protein.html`, `-recovery.html`, `-skin-redefined.html`, `-womens-health.html`, `-mens-health.html`
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

`index.html` is a hand-written redirect to `homepage.html` and is not generated.

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
requires it.

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
transformation, fifteen months apart: body fat and weight, no dates, no trend, no clinic. That is Peter's choice
(2026-09-28); his later UC Davis scans are deliberately not used anywhere. Under those two measured rows the card
also carries **pounds of fat and of lean, worked out from them and not read off the report** (fat = weight x body
fat %, lean = the rest), rounded to whole pounds: Fat 38 → 12 lb, −25 lb and Lean mass 132 → 152 lb, +19 lb. Each
figure and each change is rounded from the exact value, so a row can read a pound off its own two ends. The line
under the card says in Peter's voice that they are worked out and rounded, because +19 lb of lean in fifteen months
is at the very top of what is plausible and a DEXA lean figure carries water and glycogen besides. `PETER_SHOW_COMPOSITION
= False` takes both rows and that line off every page in one edit. Yenni's card shows fat and lean as her scans
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
- The homepage proof after the story stage: her pairs beside Peter's, then both cards.
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

The homepage runs hero → shelves → `#trending` (the scroll-scrubbed can pour) → `#story` →
`#macros` → `#consult`. `#story` is a sticky, scroll-scrubbed stage telling Peter's 15 months in
beats: his before, five product beats (each linking to a shelf), the before becoming the after,
"That's what this call is for" with a "Book a free call" button, his family, then the proof wall:
his three pairs, Yenni's two beside them, then the DEXA cards. The wall sits after the stage
(`#st-run`), so it does not make the run any longer. It is its own `<section id="proof">` with a
labelled heading, and the menu sheet's "Our before & afters" is the way to it from anywhere and from
any shelf page — the site is not getting a third fixed layer for it. The story replaced the old `#hydrate` band (its
water line now lives in the hydration beat).
Peter's lines inside it are his, verbatim, in PETER-COPY markers.

Its pace lives in two places: the `HOLD` table and the per-change lengths in the story block of
`_script.html`, and the run height (778lvh) in `style.css`. `HOLD` is
`[.9, 1.7, .45, .45, .55, .45, .5, 2, 1]`: the before, the turn, the five pack beats, the call, the
family. The pack beats are deliberately quick (a change between two packs is .8 units, not 1.5) and
their packs pile up on stage rather than swapping out; the call holds 2.0 so every flick through the
end of the story comes to rest on "Book a free call". Changing any of these means re-running the
flick test before shipping. The stage renders from an eased copy of the scroll position with
a speed cap and a backlog clamp, so a fast flick still plays each fall; it is still a pure function
of scroll, so scrolling back plays it backwards. Transforms and opacity only (a full scrub costs 0
layouts); keep it that way. Reduced motion and no JavaScript get the same beats as a plain vertical
sequence. It was tuned over four Fable review rounds; the rounds are tagged `story-round-0` to
`story-round-3`, and `PRE-STORYBOARD` is the site before it.

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

Takes ~0.05s and prints `101 products (101 with photos)` plus the per-category counts. Run it after
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
