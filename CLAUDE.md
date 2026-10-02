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

**There is no "take my stack to Amway" flow, and there must not be one.** It was built on 2026-10-01 off the
finding that Amway's attribution is session-wide, and withdrawn the same day: Peter tested it against real Amway
and a cart only ever holds the product the link opened — *"it won't add it to their cart when they go to check
out. That's no bueno."* Attribution may still carry across a session, but it buys nothing without a shared cart,
so a multi-product hand-off wastes the visitor's time and loses Peter the rest of the order. **One product
through one share link is what works**, and that is what the product card's "Buy on Amway" button does. The
rack guide's step 3 is back to "Bring it to a free call, or ask for a sample." Never rebuild the panel without
Peter re-testing Amway's checkout end to end first. (The removed code is in commit `25c619e`'s parent.)

**One source, two published sites.** Every build writes the site twice: the plain site at the repo root, and a
copy under `plus/` (`PLUS_DIR`, the name Peter chose on 2026-10-01) that carries his CCRX route. Both ship from one
push — `https://3p3t3.github.io/RAW/` and `https://3p3t3.github.io/RAW/plus/`, both indexed, Peter wants the copy
findable. He asked for a fork; one source with a switch replaced it, because two copies drift and then leak.
`CCRX = False` is the switch (`--ccrx on|off` overrides it for a run, `--no-plus` builds the plain site alone).
The copy keeps the plain file names one folder down so relative links between its pages cannot drift; `plus_links()`
(beside `demo_links()`) puts `PLUS_DIR/` on absolute page links and `../` on `assets/` and `style.css`, so there is
only ever one stylesheet. It has its own `index.html` and `site.webmanifest` so `.../RAW/plus/` opens it and an
installed shortcut starts inside it. **Never hand-edit or `Read` anything in `plus/`** — it is generated, and the
pages are the same ~310k chars as the root's. Grep them; to know why one looks a certain way, read the plain source.

**Peter's one hard constraint (2026-10-01):** peptide wording in the plain site is fine and may happen on purpose
one day, and so is the name; *"Just the link itself."* So **the guard bans hosts and the page name, nothing else**:
`CCRX_BANNED = CCRX_HOSTS + (CCRX_PAGE,)`. Every plain file goes through `guard()` on its way to disk and
`guard_root()` re-checks the root afterwards; a hit stops the build (exit 1), names file and line, and the file is
never written — verified by pasting the link into a plain template, by `--ccrx on`, and by editing `index.html`,
which the build does not write. The post-merge hook reports the same failure. If Peter ever wants the plain site to
carry the link, `guard()` is the one place to change, deliberately.

**The CCRX route** (the second, paid-referral business: an at-home blood panel and prescription compounded peptides,
fulfilled by Avellum Health). It appears in the copy and nowhere else, in three places: `#bloodwork` on the homepage
directly after `#macros`, which it echoes ("your macros you can work out; this you cannot"); the menu, **last**, as
its own small "Beyond supplements" group after the shelves (DRAFT label; it sat third until 2026-10-02, when a critic
said that gave "a paid medical referral more rank than the business the site is about"); and the footer, last. All of them go to `bloodwork.html`, never straight to CCRX — the page is where a visitor finds
out what they are walking into — and only that page links `CCRX_URL`. `site-src/bloodwork.template.html` builds it,
in the second pass only. Its order is deliberate: what the panel is → what a clinician may decide after it → Peter's
disclosure → Avellum's own statement that compounded medications are not FDA-approved drugs → the one link out.
The site-wide supplement disclaimer (`.foot-fda`) stays word for word on every page, this one included; under it,
on `bloodwork.html` only, `ccrx_fda_scope()` fills `{{FDA_SCOPE}}` (empty on every other page of both copies) with
a line in the same small print, DRAFT: "The line above is for the supplements on the rest of this site. This page is
about something different: a blood panel, which is a lab test, and peptides, which are prescription medications.
Neither is a supplement." Any new page template that fills the footer without `shared` must fill `{{FDA_SCOPE}}`
too, or the unfilled-placeholder check fails the build.
**Nothing on it says what the panel or any peptide DOES**, only what a thing is and who decides; it carries **no
price** and **nothing about where it ships** (both change, and their site states both); and it never says Amway
works with, endorses or partners with CCRX or Avellum. Peter is **paid on the peptides only, not on the panel**, so
his disclosure splits the two and is PETER-COPY: "I don't make anything on the panel. If a clinician ends up
prescribing you something after it, I'm paid on that." His Amway disclosure is a different business and is never
merged with it. Two constants beside `CCRX` expire and are each one line: `CCRX_PREORDER` (empty it the day the
first kits ship, October 10 2026, and every "pre-order" word leaves) and `CCRX_PANEL_FREE` (his "I don't make
anything on the panel", true only until the comp plan pays him on it). The route needed **no new CSS** on purpose:
anything added for it would move `style.css`'s content hash and so the `?v=` on every page of both copies.

`.gitattributes` already marks `plus/*.html` `merge=ours` through its no-slash patterns; `plus/index.html` and
`plus/site.webmanifest` have their own two lines. Renaming `PLUS_DIR` is two edits: the constant and those lines.
Publishing is unchanged: run the build, commit the root pages **and** the `plus/` folder, then RAW 0 pushes.

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
requires it. `hero-pair-240.webp` / `hero-pair-480.webp` (240x300 and 480x600, 4:5, q90, bare VP8) are the homepage hero's
portrait (`.hero-me`): **the whole 960x1200 frame of `with-daughter-960.webp`, no crop at all**, one uniform Lanczos
resize each, drawn as a 14px-radius rounded rectangle. Peter asked for it bigger and with their daughter in it
(2026-10-01: "I think I want it bigger. I think I want the whole body shot"). It renders 161x201 at 390 and 204x255
at 1440. `--pic` is `min(46cqi,204px)`; the 204 cap is what keeps the desktop hero at exactly 800px, including at
1920 where the headline hits its 104px ceiling. On phones his PETER-COPY line ("I'm Peter — husband, dad to a baby
girl, and a Lincoln local.") and the plan's two links sit at the picture's **top**, not centred against it, so the
picture's height no longer moves the button at all; what caps `--pic` on a phone is his line's column, which takes a
fourth row under ~165px. "See the game plan" ends at 830 of 844 (390x844) and 808 of 812 (375x812), unchanged by the
bigger picture. About the top two thirds of the picture is above the fold on a phone; fitting all of it would mean
dropping the headline from 58.5px to ~40px, which Peter has not asked for. Roughly a quarter of the frame's right
side is empty background (chairs, a table); trimming it would make him larger in the same box, but he asked for the
whole shot, so it is whole.
**The hero has no barbell any more** (Peter, 2026-10-01: "we might also get rid of the first bar bubble... They only
see the part at the top, and that's the part we'll keep"): no `{{HERO_BAR}}`, `.hbar`, `.hbar-cap`, `.hb-you` or
`.hb-empty`. The pinned strip (`.lbpin`) is untouched and is the only bar before the rack.

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
`#macros` → `#story` → `#my-stack` → `#consult`, and in the `plus/` copy only, `#bloodwork` sits between
`#macros` and `#story`. **`TRENDING = False`** (Peter, 2026-10-01: "maybe we should get rid of the trending
now"): the week's three best sellers are off the page. The whole section is built in `build_homepage.py`
behind that one switch and substituted into `{{TRENDING}}`, so setting it True puts the band back exactly
where it was, with its CSS kept whole. The podium is still built either way, so `bestsellers.csv` is still
read and the build still fails on a name that is not in `share-links.csv`. The 150-frame scroll-scrubbed can
pour that could ground it (`TRENDING_POUR`) went with it — markup, ~145 lines of script and its CSS; the
frames stay in `assets/pour/` and the code is in commit `8138242`. Nothing on the site now asks for those
frames, so a publish no longer needs them. The calculator moved up beside the free sample on 2026-10-01 (the game plan offers it as the
alternative: "or run your macros first"); Peter had moved it below the story on 2026-09-26 because it "came
too early" straight after the shelves; shown it again with the critic's score for it there (9/10), he chose
to keep it beside the sample (2026-10-01). Because the consult no longer follows it, the
automatic glide after "See my numbers" only runs when `#consult` directly follows the calculator's section;
the result card's own "Book a free call" carries the numbers into the form. `#story` is **a plain section**, rebuilt 2026-10-01 at Peter's request ("Instead of scrolling through it, lets
just add before and after pictures of Yenni and I side by side"). Nothing in it reads the scroll, pins or measures,
and reduced motion and no-JS get exactly the same page. It runs: eyebrow "Our story" (DRAFT) over his heading "How
we got into this" → five lines, each with the shelf link it is about → their before/afters → the ask ("The hardest
part was figuring it out alone…", PETER-COPY) with "Book a free call" and the one link across to `about.html`,
"See both our DEXA scans" (DRAFT). The lines are now in the plural: "Fatigue was a constant." (his, unchanged);
"We fixed our food and found someone to push us." and "We focused more on hydration." (his own rewrites,
PETER-COPY); "And we found ways to maximize our sleep, even during the newborn nights." and "We changed our
mornings too, and swapped our huge coffee spikes for smoother energy." (plural rewrites of his lines, DRAFT).
**His old closing line is gone whole** — Peter cut "Now I've got energy left for my daughter and my wife…" as
"unnecessary and implied with the transformation pictures", and the two sentences after it ("I didn't know how low
my baseline was…", "There's no going back.") are about his own baseline and cannot go plural without putting words
in Yenni's mouth, so they went too. They would work again only as a line of his own, in the first person.
**One pair is always out: Peter's side pair** (`.st-see`, drawn by `story_teaser()` through `his_pairs(views=('side',),
lazy=False)`; `STORY_TEASER_VIEW = 'side'`), directly under "Here's what we notice now.", with its 50% heads, "Peter ·
Month 1 → Month 15" and his caption. Peter chose it on 2026-10-02 after two critics dropped the story for showing no proof
to anyone who did not tap (phone 8.5 → 6.5, laptop homepage 8 → 7), and it also gives that heading its answer. It is not
lazy, because the hero's "Our story" link lands right on it. From 1024, `.st-top` is two equal columns: the lines on the
left, the heading and the pair on the right, which fills what was an empty half; the reveal and the ask run full width
beneath. Closed, `#story` is 1,703px on an 8,455px page at 390x844, and 1,662 on 7,070 at 1440.
**The other four pairs sit behind a reveal, closed on every arrival** — a native `<details id="story-proof" class="st-rev">`
whose summary reads "If you want to see more pictures of our real journey, they're right here." (DRAFT). It holds
`proof_wall(title=None, his_views=('front','back'))` — his front and back, then Yenni's front and back — so the side pair
never appears twice; from 760 its columns are `1fr .523fr` so his two and her two end together. `his_pairs` and
`proof_wall` default to about.html's own output, which stays byte-identical. Peter,
2026-10-01: "it opens a drop down so it stays in the same page... if they don't want to see, they can just keep
scrolling, but if they do want to see, it's right there." It is his answer to wanting both a shorter page and the
pictures. **Opening it is never scripted**: the open, the
close, Enter and Space, the expanded state and find-in-page auto-expand are all the browser's, and it works with
JavaScript off. Nothing persists its state, so every visit meets it closed.
**The one exception is its nudge** (Peter, 2026-10-01: "make the dropdown link wiggle... it sort of pops out at them
tempting them to click"; 2026-10-02: "make it 300% louder"). When the summary is fully in view, a short block just after
the `.grow` fade-in in `_script.html` gives it `.nudge`: after 360ms, for 1000ms, it lifts 6px and swells 10%, shakes like a
notification bell (−4°, +4°, −3°, +2°, −1°, 0), drops back through a smaller 4% swell, lights up `--sand` (`::before`, 1px
inside the hairline) inside a 2px `--blue` ring (`::after`, 2px outside), and the chevron dips 9px three times. It plays at
most twice — the second ~4s after the first, only while still on screen and still closed — and never again once opened on
that page view (the `toggle` event is read only to record that). Transforms and opacity only, layout shift 0 measured;
reduced motion or no JavaScript means it never moves. **`#story` carries `overflow-x:clip`** so the 10% swell can never make
a narrow phone scroll sideways (without it 320 and 390 scrolled 1-3px and the fixed `.fg` glow shifted); if `#story` ever
stops being full-width, move that clip to an ancestor that is. The knobs are the 10% swell, the 4° shake and the sand/blue
light. It is deliberately not a loop: constant motion reads as an ad and is an accessibility problem. Opening does not move the page (the
summary stays put) and the five photographs are `loading="lazy"` — not downloaded at all while it is closed, and
fetched on the toggle itself (measured, Chrome 154); re-measure if it is ever restyled with `content-visibility`.
`.grow` goes on the `<details>`, never on what is inside it. "Here's what we notice now." stays outside, leading
into the offer.
The photographs are drawn by `proof_wall(title=None)` — the same function as about.html's wall, with its own
heading suppressed; about.html is byte-identical with or without it. The five shelf links must match `PETER`
(protein, hydration, recovery, daily-foundations, energy-focus) or the build exits; `PETER_PACKS` holds the pack
picture per shelf for `#my-stack`'s key.

**What went with the stage, so nobody looks for it:** the sticky run `#st-run`, the caption strip, the
before→after wipe, the `HOLD`/`TT`/`UNIT`/`FLICK`/`CALLMIN` pace tables, the eased scrub renderer, and the flick
test (there is nothing left to flick-test). **The pinned bar no longer has a Peter mode**: the stage was the only
thing that loaded his five plates, so "Peter's stack · 0 of 5 → 5 of 5" is gone and the strip is only ever the
visitor's own stack. `#my-stack` ("That's my stack.") still draws his five, now from `PETER_PACKS`. The story's
four Fable review rounds are tagged `story-round-0` to `story-round-3` and `PRE-STORYBOARD` is the site before the
stage existed, if the old version is ever wanted. `assets/peter/side-before-480.webp`, `side-after-480.webp` and
`family-320.webp` belonged to the stage and **no page uses them now**; they stay in the repo. `assets/story/`'s
relit packs are used only by `#my-stack`'s key.

**The rack (`#goals`).** Tapping a plate opens its bay directly under that plate's ROW: `.rack` is the flex
container, `.rk-plates` is `display:contents` with `role="list"`, and `place()` in the rack block sets only
`order` (the open panel 1, the plates after its row 2), reading the row length from `--cols`. There is one copy
of each panel, so ids and aria stay single and Tab still goes plate → its panel. A notch on the panel's top edge
points at the plate. `show()` brings the plate and its packs into view together when they fit, otherwise the
whole panel (Peter, 2026-09-28: tapping a plate must show "where the items actually are").

**Section joins.** Two sections that met each laid a full `--sec` on the join, so every boundary was two of them.
`.sec + .sec,.sec + dialog + .sec{padding-top:calc(var(--sec) * .5)}` (`#story` is a `.sec` now) sits next to `.sec{padding:var(--sec) 0}`
and gives a join one full `--sec` and half the other. It applies to every page, so a new section added anywhere gets
it. `.hero + .sec` is deliberately left out.

**The rest of the homepage.** The bottom tab (`.mtab`) is phones and tablets only: hidden whole from 1024 up,
where the header nav already carries MACROS. The quick-call card that sat under the sample form is gone;
`#quick-call` now marks the consult's `.wrap.split` until a sample is sent, when the script hands the id to the
thank-you's call invitation, so the game plan's step 05 link still lands. From 768 the sample section's text is centred vertically against its card. The sample form's shelf picker uses
container queries so the ten sit evenly (two a row on phones, five on the desktop card). **The booking card (`#consult-form`) asks one question at a time**, on the macro calculator's own machinery so
the two cards read as siblings: a step counter, three progress pips, a `Back` link, and a Continue button that
reads the card's own "Pick a time" back on the last step. The three steps are the question blocks it already had,
in the order it already asked them — the five goals, Peter's six training answers, then both blanks in one
fieldset whose legend is furniture and visually hidden (its two field labels are the real questions, and those
could not change). `cStep()` in `_script.html` owns `[hidden]`; the markup hides steps 2 and 3 so nothing flashes,
and `html:not(.js)` puts them all back with the furniture away, so a no-script visitor gets the single card it
always was. **Not a word of a question, an answer, a label, a placeholder or the button changed**; the only new
copy is the furniture and two validation lines, all DRAFT-COPY.
**A picked chip advances by itself**, and telling a real choice from a look is the trick: Chrome fires a full
`click` on every radio the arrow keys walk past (measured, Chrome 154), so a visitor reading Peter's six training
answers with the arrows would be carried off the step. What a pointer carries is `e.detail` — 1 for a mouse click
or a touch tap, 0 for anything a key synthesised — so a pointer advances on `detail`, and of the keys only Space
does, through its own keydown. **Re-measure that if the Chrome version moves**, and note a scripted `.click()`
deliberately will NOT advance, so test this with `Input.dispatchMouseEvent`, not JavaScript.
Answers and the step survive a reload under `aspire-consult` (its own key, so the calculator's "Start over" cannot
orphan it). **Steps 1 and 2 now require an answer** where the form could once be submitted blank; both blanks on
step 3 stay optional, and the last step re-checks the steps above it. Arriving from the calculator lands on step 2,
because the goal above has just been filled in.
The five goal chips sit two across below 1024 (they each took a whole row with half of it empty). From 1024 the row
already took three and two, so that block is untouched and its measured laptop fit still holds: the card was 745px
at 1440x900 with every question showing, and is 507-615px by step now. At 390x844 `#consult` went from 1458px to
720/888/793 by step. Re-measure if a question is added or reworded.

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
