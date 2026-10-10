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
- `site-src/style.css` — copied to `style.css` at the repo root at build time; every page links it via
  `{{STYLE}}`, which the build fills in with a content-hash query string. It sits at the root, not under
  `assets/`, so its `url(assets/...)` backgrounds keep resolving against the page's own folder
- `share-links.csv` (`product,share_link,photo`) — the product list, 105 rows
- `bestsellers.csv` (`product,units_this_week`) — top 3 rows become the podium; `product` must
  match a `share-links.csv` name or the build exits. Blank `units_this_week` just hides the count.

Generated (never hand-edit; the next build overwrites them):
- `shop.html` (Tab 1, Shop, from `site-src/shop.template.html`, the page the site opens on and where the curtain plays)
  and `homepage.html` (Tab 2, Our approach); see "Two tabs" below. `bloodwork.html` is generated on both copies now.
- `about.html` — the About us page, from `site-src/about.template.html`: their two portraits, who they
  are (`peter_text`, and the same `her_text` block the Women's Health shelf carries), the proof wall
  (`proof_wall`: his three pairs and her two), both DEXA cards, then the free sample and the call with
  the closing block. It is where the menu's "About us" goes, from every page, and — since 2026-10-05 — the footer's
  own "About us", which leads the footer link row. The menu was its only link anywhere, and the menu button is
  `display:none` from 1024 up, so on a laptop this page could not be reached from the site at all. The row is five links
  now, so it keeps its own full-width line up to **1279** (it was 1199) and is a wrapping flex row in that band, not one
  grid row: at 768 the five would have run 10px past the window's edge and scrolled the page sideways. The proof used to
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

**"Recomp" is no longer a goal (Peter, 2026-10-07: "can we get rid of recomp as an option on the macro calculator?").**
The radio, its factor in `mcCalc` (`tdee * 0.92`), its place in the `noRoom` test, its note in `MCGOAL` and its row in
`MCTOC` are all gone; `docs/macro-calculator.md` records what it did and strikes through its worked example. **mcCalc
is 2,284 chars now, not 2,333** — that is a deliberate change, the first since the figure was pinned, and the maths for
the three remaining goals is provably untouched (only a branch of one ternary and one `||` clause left). A returning
visitor with `goal:'recomp'` still in `aspire-macros` falls back to **Maintain**, checked and with no console error —
verified. The goal step dropped `cols` and stacks in one column, like "Where are you at with training?", the other
three-option step; three in the two-column grid left a hole beside the third.

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

**Superseded 2026-10-03 (see "Two tabs" → providers and guard, below, which wins wherever these two paragraphs
disagree):** the guard now bans only `ccrx.health` on the plain site, and the bloodwork route is on both copies.

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
prescribing you something after it, I'm paid on that." His Amway disclaimer was a different business, was never merged
with it, and is **off the site** (see below). Two constants beside `CCRX` expire and are each one line: `CCRX_PREORDER` (empty it the day the
first kits ship, October 10 2026, and every "pre-order" word leaves) and `CCRX_PANEL_FREE` (his "I don't make
anything on the panel", true only until the comp plan pays him on it). The route needed **no new CSS** on purpose:
anything added for it would move `style.css`'s content hash and so the `?v=` on every page of both copies.

`.gitattributes` already marks `plus/*.html` `merge=ours` through its no-slash patterns; `plus/index.html` and
`plus/site.webmanifest` have their own two lines. Renaming `PLUS_DIR` is two edits: the constant and those lines.
Publishing is unchanged: run the build, commit the root pages **and** the `plus/` folder, then RAW 0 pushes.

(`.gitattributes` also carries `shop.html merge=ours`, which matches `plus/shop.html` too, and `bloodwork.html merge=ours`: it is generated but no other pattern matched it, and it
conflicted on the 2026-10-02 merge.)

**No Amway disclaimer on the site (Peter, 2026-10-04).** "Disclaimer: I'm sponsored by Amway and paid based on products
sold." (PETER-COPY) used to sit in `#consult` on the homepage and in about.html's closing block. Asked whether to add it
to the Shop as well — now the landing page, and the page with the product links — he said *"no get rid of it in the our
approach area as well"*, and then chose "everywhere" from the three options. **He decided that having been told first
what the line is for**: a paid endorsement under the FTC's endorsement rules, and that Amway's own IBO rules may require
an IBO to identify themselves on their own site, which he was advised to check with his Amway compliance contact. So it
is his call on his own business, recorded here, **not an oversight — do not restore it without asking him**, and do not
write a replacement disclosure unprompted. What remains, untouched on every page of both copies: the footer's
fulfillment line ("Checkout, fulfillment and delivery occur through our partner vendors, Amway or Avellum Health.") and
the FDA supplement disclaimer (`.foot-fda`). Both templates keep a short comment where the line was. The Avellum/CCRX
disclosures are a separate business and are unaffected.

`index.html` is a hand-written redirect to **`shop.html`** (since 2026-10-04) and is not generated; the build copies it
verbatim into `plus/`. It carries no hash, so the curtain plays on arrival.

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
requires it. **Since 2026-10-03 the homepage hero is Tab 1's `.hh` (see "Two tabs"), where `hero-pair-240.webp` is a small
signature at the hero's foot, and since 2026-10-05 the SHOP hero's foot carries the same block (`.sh-me`); the paragraph below describes the old film hero's `.hero-me`, which no page uses now and
whose CSS is gone.** `hero-pair-240.webp` / `hero-pair-480.webp` (240x300 and 480x600, 4:5, q90, bare VP8) are the homepage hero's
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

## Two tabs: Our approach and Shop (2026-10-03)

Peter, 2026-10-03: "this just feels too busy. Maybe we split the tabs. 1 tab is for products, 1 tab is to bring people
through the story and book a call". This section wins over anything older below that disagrees with it.

**Shop first (Peter, 2026-10-04): "Can we swap it so my shop appears first, and then the, our approach is actually the
second tab?"** Asked how far that went, he chose the Shop as the page the site opens on, with the curtain moved onto it.
So the tab bar reads **Shop, then Our approach**; `index.html` opens `shop.html`; the masthead and footer wordmarks and
the About/bloodwork brand labels all point at `{{SHOP}}#top`; and `{{INTRO}}` lives in `shop.template.html`, filled at the
shop's build block. Everything about the call still lives on the approach tab (`homepage.html#consult`, the mobile tab's
links, `quick_call`), and `_intro.html` itself is byte-identical — not a beat re-timed.

- **`homepage.html` (Our approach, Tab 2):** `.hh` hero → `#story` → `#why` → `#macros` → `#how` → `#consult`. No curtain.
  7,237px at 390, 5,781 at 1440 (it was 8,456 at 390 as one page).
- **`shop.html` (Shop, Tab 1, `site-src/shop.template.html`):** the curtain → the square film hero ("Pick your goal" → `#goals`, "Ask for a free
  sample" → `#sample`) → `#goals` → `#sample` → `#my-stack` → `#results`. The rack never opens on ten closed plates:
  the first plate on the visitor's bar, else the rack's first, starts open, quietly (no scroll, no sound). Under the
  guide, "Browse all 105 products" (`.rk-all`, `data-all`). **`#results` is grouped by shelf** (2026-10-04, two critics: it
  was one flat 16,000px grid): one `h3` and list per shelf in PLATES rank (Protein first), each product once under its
  `cat_of` home shelf, over `#g-jump` — ten shelf links, no JS needed, sticky under the masthead (and under `.lbpin`, and
  under the phone search row via `--srch`), the shelf in view lit — and "Back to the shelves" (→ `#goals`) after the last
  row. A search hides a shelf that has no match, heading and jump link together; `showAll()` clears the search box.
  **Peter's five packs in `#my-stack`** are links now, each captioned with its product name and opening that product's
  `#pcard`: `PETER_PICKS` maps shelf → product and the build exits on a name that is not in `share-links.csv`.
  The shop hero's headline steps down at ≤480px and its lead moves below the links (CSS `order`), so "Pick your goal" ends
  at 654 of 844 at 390 and 576 of 640 at 320 (it was 799 and 723); the square film is untouched.
  **The film's play/pause is out of the way, not gone** (Peter, 2026-10-09: "Can we remove the play and pause button
  for the hero video?", then, offered a hover-only version, "do the hover one"). `.glass-toggle` is always in the DOM
  and always in the Tab order; at rest it is `opacity:0;pointer-events:none`, and it fades in on a hover anywhere over
  `.glass` or on its own `:focus-visible`. **Never swap that for `display:none` or `visibility:hidden`** — either takes
  it out of the Tab order, and this is the page's one way to stop motion that starts by itself and runs over five
  seconds (WCAG 2.2.2; the film loops). **On a touchscreen it never appears** (Peter, 2026-10-09: *"remove the
  paly pause button on touchscreens as well"*). A `@media (hover:none){...opacity:1}` rule used to keep it
  visible where there is no hover; **he was told that removing it leaves a phone with no visible way to stop
  the film, and chose it anyway. It is his call on his own site — do not restore that rule without asking
  him.** The button stays in the DOM and in the Tab order on purpose, so a tablet with a keyboard still
  reaches it (verified under touch emulation: `0` at rest, `1` with `:focus-visible` on a keyboard focus). Measured: at rest `0 / none`, hovering the film
  `1 / auto`, mouse away `0 / none` again, keyboard focus `1` with `:focus-visible` matching, and the click still
  pauses and relabels. Three other things carry the same load and must stay: `prefers-reduced-motion` is read
  **before `play()` is ever called**, so a visitor who has asked their system for less motion gets the poster and the
  mp4 is never fetched (verified: no `src` at all); the film is muted with no audio track, so it owes no captions; and
  it pauses itself off screen and in a background tab. **Testing it needs `#top` on the URL** or the curtain covers
  the hero and every hover lands on `.intro-stage`.
  **At the shop hero's FOOT, since 2026-10-05, Peter signs it**: the same `.hh-me` block Tab 1's hero carries — his 60px
  photograph (`assets/peter/hero-pair-240.webp`) and his PETER-COPY line verbatim — with the homepage hero's own "See how
  we did it" (→ `homepage.html#story`) beside it. Three critics found that the page the site opens on never said whose
  shop it was: the first "Peter" and the first "Lincoln" were two thirds down, in the sample form's "Hey Peter, I'm ___".
  Nothing is new wording and the CSS is shared; `.sh-me` only swaps the colours, because this hero stands on the chalk
  field where Tab 1's stands on a photograph (the line 13.1:1, the link 12.8:1, measured on the rendered pixels). It sits
  **below** `.hero-copy`, so the film does not move and "Pick your goal" keeps 654 at 390 and 576 at 320, to the pixel.
- **Cross-links:** `#how` steps 01/02 go to `shop.html#goals` / `shop.html#sample`; its own button is **"Book a free call"
  → `#consult`, on this tab**, since 2026-10-05 (it was "Ask for a free sample" → `shop.html#sample`, which sat ~170px
  above the booking card and pushed a visitor who had just read the plan back to the shop they arrived from), with the
  sample demoted to the quiet link beside the calculator's. The block is only in `homepage.template.html`, so the shop and
  the shelf pages are untouched. `#my-stack`'s and the
  thank-you's call buttons and the rack guide's "free call" go to `homepage.html#consult`, and `#my-stack` carries a third,
  quiet "See how we did it" → `homepage.html#story` (2026-10-05): it opens on "From our story" and draws his five packs,
  but since the split the story is on the other tab and nothing in the section went to it. Search, `?q=`, `?try=`, the
  sample's `_next` (`shop.html?sample=sent#sample-sent`), "All products" and `data-all` all go to shop.html; shelf pages
  call `card_dialog('shop.html')`; `quick_call(home)` takes the way home. `#quick-call`'s hand-over on the sample's
  thank-you only happens on shop.html (it has no consult). The pinned strip (`.lbpin`) shows on both tabs once there is
  a stack and reads names from `data-plates` where there is no rack, which keeps the call note's "Interested in:". It
  carries **"Bring it to a call"** (`.lbpin-go` → `#consult`, or `homepage.html#consult` off the homepage) at its right end,
  and from 768 its label names the plates when they fit, else counts them.
- **The stack carries the product, not just the shelf (2026-10-04).** "Load this plate" inside a product's `#pcard` (the
  rack's packs only — the grid's and `#my-stack`'s cards still don't offer it) stores that product's exact listing name in
  `aspire-stack-picks` beside the shelves-only `aspire-stack`, which keeps its old format, so stored stacks still read.
  Then the call note reads "Interested in: Recovery (XS Muscle Multiplier - Berry Blast), Hydration." and the sample's
  blank prefills that name. Loading from the rack itself carries no product and reads as before; taking a plate off clears
  its product; nothing is ever sent to Amway, and typed text is still never overwritten.
- **The tab switch (`.tabs` in `_header.html`, every page, labels DRAFT):** `{{SHOP}}`, `{{TAB_HOME}}`, `{{TAB_SHOP}}` are
  filled by `nav()`; shelf pages take `nav()`'s `'shelf'` mode and light **Shop** (`aria-current="true"`, not `"page"` —
  the shelf is not that page), while About and bloodwork.html light neither. Below 1024 it is the masthead's second row (`--tabh:40px`; `--mh = --mast + --tabh` = 100px; anchors
  and `.lbpin` use `--mh`, `--mast` is unchanged). From 1024 it is a two-part pill and the inline nav is **Macros · Book a
  free call** ("Products" went on 2026-10-04: it and the Shop tab opened the same page; the menu and footer keep their
  "All products" links). With one item fewer the wordmark's name now shows **from 1100** (every gap 24px at 1100/1200/1279)
  and hides only at 1024, where search would still run under the nav.
  Both tabs carry `#top`, so the curtain never replays on a switch; it never plays when a page opens at an anchor, and
  only a bare arrival (`/` → `shop.html`) shows it. `<title>`/`og:title` on the shop are brand-first now that a shared
  link resolves there: "Aspire Health · Shop" and "Aspire Health" (DRAFT).
- **Tab 1 hero (`.hh`):** "Feel better. Know why." (PETER-COPY, chosen 2026-10-03 over "Stop guessing. Start knowing." and
  his first, "Feel your best. Understand why."), label "Aspire Health" above it (below 420px the masthead shows the wave
  alone), a DRAFT sub-line, then "See how we did it" → `#story` and "Book a free call". Peter's photo and his PETER-COPY
  line sit at the hero's **foot** as `.hh-me`, small (60px phone, 68px from 768) under a hairline (Peter: "my photo should
  actually be more towards the bottom... lets the lake speak for itself more"). Behind it: `HOME_BG` (`assets/home/lake.webp`,
  the lake at dawn, fal-generated, 2400x1340) and, on phones, `HOME_BG_PHONE` (`assets/home/lake-tall.webp`, its own tall
  frame, top 30% cropped off so the horizon sits high), through a `<picture>` in `home_bg()`; `HOME_BG_FOCUS` maps each path
  to (desktop, phone) object-position. Empty `HOME_BG` draws the palette ground `.hh-ph`. The copy carries its own scrim, so
  readability never depends on the picture: measured on the real photos, lowest 5.43:1 (320/390/768/1440). Both files are
  placed by hand; the build never writes them.
- **A fact row under each hero (`.hfacts`, 2026-10-08).** Three countable facts, no claim, Peter's own wording and his
  own middle dots (drawn in CSS between the cells, so a screen reader meets three list items, not punctuation). One row
  per tab, because the tabs say different things: the Shop's is "100 options · 10 goals · 1 free sample", Our approach's
  is "1 blood panel · 10 goals · 1 free call" (both DRAFT). **They are not links** — each hero already carries its two
  ways on and "one ask per phone screen" stands, so the row is there to be read. In both templates it is the LAST row of
  `.hero-copy`, after `.hero-actions`: that is what keeps the Shop's first screen untouched ("Pick your goal" still ends
  at 654 of 844 at 390 and 576 of 640 at 320, measured) and what puts the homepage's row inside the hero's own scrim, so
  it is never read straight off the photograph. Below 480 the Shop's row takes `order:2`, under the lead that the same
  breakpoint moves below the links. It sets **no colour of its own** and inherits the hero it stands in — `--text` on the
  Shop's chalk field (5.9–6.6:1), chalk on Tab 1's scrim (8.4–15.3:1), measured on the rendered pixels — so neither row
  can drift from the copy above it. **The "100" is the one number on the site that is not counted**: `SHOP_OPTIONS` in
  `build_homepage.py`, hard-coded on Peter's instruction (2026-10-08) because he is curating the catalogue to exactly
  100 and wants a number that does not drift while he does it. It counts *listings* (flavour variants included), which
  is why the cell says "options": the 105 rows today are 68 distinct products. While it and `share-links.csv` disagree
  **every build prints a note** saying so — a note, never a failure, since 105 rows today would otherwise block him —
  and the footer's "All 105 products" is still counted from the data. **That gap is Peter's decision, already taken: do
  not reconcile them**, change the constant the day the list is trimmed. The goals are counted from `CATEGORIES`.
- **The lake through the day (Peter, 2026-10-03):** the same shore three times — dawn in the hero, clear morning at the
  top of `#why` (`.why-band`, `assets/home/lake-morning.webp`), and dusk behind the
  call (`.consult-dusk` / `.c-dusk`, `assets/home/lake-dusk.webp`). Both were made with fal kontext/max from the hero's
  own frame (`~/Desktop/aspiree/tools/jobs-lake-tod.json`, picks `lake-morning-2` and `lake-dusk-1`), then 2x ESRGAN
  (`jobs-lake-tod-up.json`) and exported 2400px. **The morning one is `#why`'s own header now (2026-10-08)**, not a strip
  above it: Peter, "this feels too light. We should swap it for a darker photo or different option. Or we can skip it
  altogether and go straight into it." It had been a pale picture with nothing written on it between the cream story
  above and the cream pillars below — 420px, then `clamp(220px,17vw,300px)` after a critic called it dead space — so it
  lightened an already light page and pushed the copy down. All three ways out were drawn and compared (cut it; swap the
  frame for the dusk one; keep the frame and put the head on it) and the third shipped, because it is the only one that
  turns the space into something: `.why-top` is a dark band holding the picture (`.why-band`, now `position:absolute`
  and framed on the water, `object-position:50% 72%`, 76% from 768) under a scrim, with `.why-head` — the eyebrow, the
  h2, Peter's argument, the two lines and `.why-door` — set on it in chalk. The pillars, the roles line and the
  disclosure stay on the light ground in a second `.wrap`. It did NOT fix the two critics' other finding, that the h2
  and the argument read as two stacked headings, but it contains it: the pair is now one title block over a picture with
  the pillars clearly below, instead of two competing headings in one cream column. The accent `.hl-k` goes `--sand` on
  the band, because the XS blue is a black mark there. Markup is `why_section()` in `build_homepage.py`.
  From 768 the dusk picture is drawn 140% wide and set 40% left so the
  afterglow sits under the copy, not behind the card; on phones it is its own strip above the heading; and
  `.c-dusk::after` fades to the section's own `#141A26` over its last 200px and `body:has(.consult-dusk) .foot` starts
  there too, so there is no seam and no pale band between dusk and night. On phones the strip is `clamp(140px,41vw,180px)`
  and a negative `scroll-margin-top` on `.consult-dusk` cancels it, so arriving at `#consult` lands on the eyebrow (116px
  at 390) with the heading and every goal chip on the first screen, instead of on 316px of lake.
  The Shop tab has no lake, on purpose: its film is its own look.
- **`#why` opens with Peter's argument (2026-10-06), which the site had been missing.** He described it in his own words
  — "bloodwork will feed supplements. our bloodwork will show what people are actually deficient in, so when they get a
  supplement they know its one that meets a real need" — and a check found nothing on the site said it: "deficien*"
  appeared **zero** times in the whole source, and the closest copy ("the few products that fit your goal", "you don't
  need bloodwork to try anything") was about goals and about checking afterwards, never about the panel telling you what
  to take. It is the one argument that separates his shop from anyone else with the same Amway catalogue. It now leads
  the section as `.why-arg`, in the display face, because at body size it read as the first of three paragraphs:
  **"Remove the guesswork. Start with your bloodwork."** (PETER-COPY) over "A panel shows where you actually stand. Then
  what you take is a decision, not a guess." It pays off his ask ~4,000px below, which is the same problem from the
  inside ("testing supplement after supplement to find what worked"). **CLAIMS: it promises KNOWING, never treating.**
  A panel shows where you stand; the site never says a product corrects what the panel found, which would be a health
  claim and is what the FDA line on every page and his own copy rules keep away from. Never tighten it into one.
  The third line replaced "You don't need bloodwork to try anything…" (Peter, 2026-10-06): **"Bloodwork comes first for
  any peptide protocol — a clinician needs it before they can decide. For supplements it's recommended, not required."**
  The requirement is the clinician's, which is why it is worded that way and matches the roles line; supplements stay
  ungated, which is his standing rule.
- **`#why` ("Understand why", built in `build_homepage.py`):** lead, four pillars (Know your numbers, Build and keep lean mass,
  Fuel it, Peptide protocols — **always that order, on both copies**: Peter, 2026-10-04, "we should be building this as if
  it's live. this is the beta meant to be for Nov 2nd launch when its all live", so the bloodwork content is never demoted,
  folded or reordered for not being live yet. The only pre-launch signal is his PETER-COPY line on the two provider cards,
  "We are currently in the early access phase only. We will go live for all clients November 2nd.", which leaves by itself
  with the empty link; if November 2 passes without a link, change it), the roles line ("licensed clinicians read your bloodwork… I don't read labs and I don't
  prescribe"), then the disclosure. All DRAFT. Bloodwork is the ideal, never a gate (Peter: "I don't want them to have to get
  bloodwork to try a product or buy a product"). The bloodwork is collected at home with a **Tasso** (`TASSO`, in both
  providers' copy); never call it painless or FDA-cleared unless Tasso's own site says so.
- **Who actually runs the panel (checked on their site, 2026-10-08; ownership corrected by Peter the same day).**
  **Valdura is owned by Avellum** — not a third party, which is what the first pass here assumed from their public pages.
  So the panel, the app that reads it and the route are one company wearing two names: Avellum's banner says "a blood panel
  from Valdura", Valdura takes the payment and holds the results in its app, and the lab work is Better Human Labs'. The
  practical consequence is that the plain copy should not imply a hand-off to a stranger; it may name Valdura as Avellum's
  own app, or skip the name and say "their app". The plain copy said "measured from your own blood, through Avellum Health", which claimed the panel was
  theirs; it now says you reach it through Avellum and the panel is Valdura's. **Neither site states a biomarker count and
  neither should:** Avellum, the panel page and Valdura's own "what we test" page give no figure anywhere. What Valdura lists
  is ~17 drawn markers (ApoB, Lp(a), lipid panel, HbA1c, homocysteine; albumin, ALP, ALT, cystatin C; ferritin, vitamin D,
  B12, hs-CRP; TSH, free T3, total testosterone, SHBG) plus 3 calculated — and "lipid panel" is itself several, which is
  probably why they print no number. A count may only go on the site if a provider states one in writing, and then per
  provider, since the two copies route to different ones. **Peter settled the subscription question (2026-10-08):** "its not a
  subscription btw, the ai agent is, but the bloodwork isnt and you dont need to do both." So the panel is a one-off and the
  Valdura app is the optional recurring thing — the plus copy's "You pay for it once — it isn't a subscription" is correct and
  stays, and nothing on either site may imply the panel itself recurs. Avellum's own panel page says the same ("One-time
  payment, not a subscription"), so it is a verified fact of the plain route too — and since 2026-10-08 the plain copy
  carries it in its own words, scoped to the panel because the app bundled with it is the recurring thing: "The panel
  itself is a one-time payment, not a subscription." The two CCRX sentences beside it ("No prescription to get first. No
  appointment to sit through.") are still storefront facts not known of this route and stay out. **"A licensed clinician reads it" is wrong and Peter has accepted that (2026-10-08).**
  Valdura's own homepage: "Valdura is an AI health assistant that reads your bloodwork… The clinical calls go to your own
  clinician", the panel needs no telehealth visit, and the assistant hands anything prescription-adjacent to the visitor's
  own clinician instead of deciding. Valdura also publishes the count the rest of the sites do not: **20 biomarkers + 3
  calculations** in the Longevity Panel, and the membership is $59.99/month, bought separately from the panel. Two of their
  own lines are usable and strong: the plain-English read of every marker, and "The assistant is not allowed to sell you
  anything." Peter says **Avellum's medical director helped shape the AI**, which is his to assert — but it is ONE director,
  so "designed by doctors" overstates it where "designed by a doctor" does not, and it is a claim about a partner's product,
  so it wants to be something Avellum would repeat. **Peter is not Avellum: "our proprietary AI" is wrong on his site
  whatever the ownership.** Peter approved "doctors" plural on 2026-10-08 and gave the grounds: one medical director plus a
  team of MDs who support him, "and we're involved in the direction of the app" — so it is not one person and the plural
  stands. **APPROVED, TO BUILD** (held only until the site-wide glass lands, because it is in the same functions):
  - `why_section()` card 01, replacing "…It goes through {provider}, and a licensed clinician reads it, not me.":
    "Bloodwork is a lab test: your biomarkers, measured from your own blood, collected at home with a Tasso. It goes
    through {provider}. Designed by doctors, explained in English: their assistant reads every marker back in plain words."
  - the roles line, replacing "Who does what: licensed clinicians read your bloodwork and decide on any protocol…":
    "Who does what: an assistant reads your bloodwork back to you in plain English, and anything clinical goes to a
    licensed clinician, who decides on any protocol and can say no. I don't read labs and I don't prescribe. My part is
    your nutrition and the products."
  - the Our approach fact row becomes **"1 panel · 20 biomarkers · 1 free call"** (Valdura publishes 20 biomarkers + 3
    calculations on its homepage, so the count is citable at last; it is per-provider in principle, so if the plus route's
    panel ever differs it needs its own number).
  **The third "clinician reads it" in `bw_parts()`'s `after` is CORRECT and must not be touched** — there "it" is the
  intake form, not the panel: "You fill in an intake. A licensed clinician reads it and decides whether a prescription is
  appropriate for you." Only the two above are wrong.
- **Providers and guard:** both copies carry the bloodwork route (`#why`, `bloodwork.html`, the "Beyond supplements" menu
  group, the footer link, `{{FDA_SCOPE}}`). `provider()` / `bw_parts()` pick it: plain → **Avellum Health**, plus → **CCRX**
  (copy unchanged). Peter is **not paid** through Avellum (`AVELLUM_PAID = False`, `avellum_disclosure()`: "I don't make
  anything when you go through to Avellum Health, on the bloodwork or on anything a clinician prescribes."). He has no
  Avellum link until about 2026-11-01, so `AVELLUM_URL`, `AVELLUM_PANEL_URL`, `AVELLUM_PROTOCOLS_URL` are empty and every
  Avellum button reads "Coming soon"; going live is `AVELLUM_URL = '<link>'` and a rebuild (only avellumhealth.com links are
  accepted, and a link with `AVELLUM_PAID = None` refuses to build). The plain bloodwork.html drops the CCRX storefront facts
  not known of Avellum (pre-order, pay once, 28-day refill). `GUARD_BANNED` is `ccrx.health` plus `CCRX_URL`'s host, with
  Peter's quote ("Avellum links can go on the regular site, crystal clear links will go on the plus site. Both still want
  the split."); `write_plus()` refuses `avellumhealth.com`. Verified 2026-10-03 by five forced failures, all exit 1: the CCRX
  link in a plain template, `--ccrx on`, the link in `index.html`, `AVELLUM_URL` with `PAID = None`, and an Avellum link
  reaching plus. `#bloodwork` and `ccrx_home` are gone; `ccrx_block`, `ccrx_menu`, `ccrx_fda_scope` keep their names but
  serve both copies.

## The glass (2026-10-08)

Peter: *"I think the glass should go site-wide."*

**Glass here is a tinted panel over a picture, and both halves are load-bearing.** The tint — `rgba(0,46,59,.72)`,
Peter's own teal — is what guarantees the contrast, because every word then sits on a colour we control whatever the
picture does. The blur, `backdrop-filter:blur(24px) saturate(1.1)`, is declared **on its own inside `@supports`**, so
the tint alone is the fallback and the panel reads as well with no blur at all. The card keeps its own character; only
the hand it is written in changes, ink-on-chalk to chalk-on-teal, with pills inverting to sand-on-teal so they still
have shape.

**Glass goes where there is a picture. Nowhere else.** The site's ground is `.field` — one fixed sheet of chalk with
two drifting glows and a grain — and there is no detail in it to refract, so a blurred panel on the chalk is an
invisible change sitting on a backdrop that moves. **Do not put glass on a chalk section**, and do not put a texture
behind one just to create an excuse for it: a bare heading on `tex-water`'s brightest ripple measures 1.0:1.
Where a dark band is wanted, the recipe is a picture + a scrim deep enough to be the floor + chalk copy, measured.

Where it is, and what each one stands on:

| Panel / band | Stands on | Treatment |
|---|---|---|
| `#consult-form` (homepage) | `lake-dusk.webp` | the original: teal tint + blur, note-card shape (`.nc`) |
| `.mc-card` (`#macros`, homepage) | `tex-water.webp` + scrim | the same tint and blur, its own plain sheet shape |
| `.why-top` (`#why`'s header, homepage) | `lake-morning.webp` + scrim | ground only — copy direct on the band |
| `.sec.dark.mys` (`#my-stack`, shop) | `tex-water.webp` + teal tint | ground only — no panel to glass |
| shelf heroes (`.cat-hero`) | their own banner + scrim | already this language; left untouched |

**`assets/home/tex-water.webp` (76 KB, 2000x1116)** is the brand-teal water macro, the calmest of the three textures
that were sitting unused. It is a **CSS background**, not an `<img>`: no markup, it reaches `plus/` and the templates
untouched, and it is fetched off the layout pass rather than blocking the first paint. `url(assets/…)` in `style.css`
resolves against the **stylesheet**, which sits at the repo root, so `plus/`'s `../style.css` finds the same one file.
It is the only texture in use and it is **one per page**: `#macros` on homepage.html and `#my-stack` on shop.html,
so a visitor who crosses between the tabs pays for it once. `tex-gel.webp` and `tex-ice.webp` are still unused;
`tex-ice` is the brightest and least even and would need a much deeper scrim. Every band keeps a **solid dark floor**
under its picture, so a webp that never lands changes no measurement.

**What is deliberately left flat, and why** — do not "finish the job" by glassing these:
- **the Shop's square film hero, the product grid (`#results`, `.cat-shop`) and the product card dialog**: a busy
  catalogue behind glass is noise, and the packs are the content;
- **the rack (`#goals`)**: ten coloured plates and a sand hollow (`.bay`) that is already a crafted surface;
- **the DEXA cards and the proof wall on about.html**: evidence, on chalk, with no picture behind them. The old
  `.mc-card` comment had the right instinct for the wrong reason — "a backdrop that changes underneath would make
  those measurements a guess" — and the tint is the answer to it, but these cards have nothing to look through;
- **`bloodwork.html`**: the disclosure page, plain white cards on chalk, and it should stay plain;
- **the free-sample card (`#sample .c-card.nc`)**: it is the same shell as `#consult-form`, light instead of dark, and
  that is the same card in two lights rather than a clash. Darkening it would need a second dark band immediately
  above `#my-stack` — about 3,400px of unbroken dark at 1440 on the page the site opens on — and would cost the Shop
  its one warm, handwritten surface. A prototype exists in RAW 84's report if Peter wants to see it.

## The story (`#story`)

**(Order superseded 2026-10-03: see "Two tabs" above. Lines superseded 2026-10-04: "Fatigue was a constant." (PETER-COPY),
then "New baby, no sleep, no energy. So we changed a few things." (PETER-COPY), then "Here's what we changed." over the
five shelf names alone as a ruled list of big links (`.st-shelves` / `.st-go`; Peter: "we shouldnt explain the sections");
the four sentences that sat over the links are kept in the template's comment. "Here's what we notice now." is now
"Fifteen months later." (PETER-COPY).)** The homepage runs hero → `#story` → `#how` (the five-step game plan) → `#goals` (the plate rack) → `#sample` →
`#macros` → `#my-stack` → `#consult`, and in the `plus/` copy only, `#bloodwork` sits between `#macros` and
`#my-stack`. **The story comes straight after the hero** (Peter, 2026-10-02: "should I put the story towards the top?
That way they know when they get to supplements it's about finding the ones that will support their
transformation?"; a Fable critic's first finding was that he "arrives too late on his own site"): proof, then the
process, then the products. Let the order make that connection — the page never says supplements caused the
change. The hero's main button reads "See how we did it" and goes to `#story` (it said "See the game plan" and jumped
over the story); the game plan's eyebrow is "Where to start" (was "New here?", which came late after a whole story);
`#my-stack` carries a "From our story" eyebrow over "That's my stack." because it now arrives ~4,000px after the
story, and its first button is "Load your own plates" → `#goals` (it pointed back at the calculator just passed).
All four are DRAFT and Peter-approved. `.story + .how-sec` puts a hairline over the game plan's heading, so the plan
reads as a framed stretch between the story above and the rack below. `#story` starts at 934px at 390x844 and 876 at
1440; his side pair's photo is at 1,915 and 1,393. **`TRENDING = False`** (Peter, 2026-10-01: "maybe we should get rid of the trending
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
beneath. Closed, `#story` is 1,703px tall at 390x844 and 1,662 at 1440.
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

**The open bay is TEAL GLASS (2026-10-09).** Peter, after the flat dark slab shipped: *"could we do a glass
colored teal? it has that glassy/transparent feel"*. It follows the house recipe exactly — a tint of his own
teal that is itself the contrast floor, with `backdrop-filter:blur(20px) saturate(1.12)` declared on its own
inside `@supports`, so the tint alone is the fallback. **The alpha was measured, not eyeballed**: composited
over the chalk field, **0.90 is the lowest that keeps every piece of copy at 7:1 or better** (0.86 drops the
line under the title to 6.26, 0.74 breaks 4.5). It ships as a `.93 → .90` gradient with a lit top edge
(`inset 0 1px 0 rgba(255,255,255,.20)`) and the sand rim. On rendered pixels, 56 measurements across two
widths and four shelves: **worst 7.53:1, and identical with `backdrop-filter` forced off** — which is the
proof that the tint is carrying it. **Be honest about the blur here**: there is no photograph behind the rack,
only the field's grain and its two drifting glows, so the blur is faint and most of the glassiness is the
translucency, the lit edge and the rim. That is also why this does not break "glass goes where there is a
picture" the way a bare `backdrop-filter` would — the tint, not the blur, does the work. If the alpha moves,
re-measure on rendered pixels with the blur forced off.

**The packs were landing on the heading, from 1024 up (fixed 2026-10-09).** Peter: *"looks like the words are
getting cut off, maybe thats the case for mobile too"* — **it was not mobile**, and nothing was clipped: the
pack images are drawn **1.42x and hauled up by 91% of the overflow** (`.bay-go img`, in the 1024 block) so the
row keeps its original height and the pack stands proud of it, and that pull is **47.4px**, which put the
tallest pack's top over the line under the title. Measured: the highest pack overlapped by **31.4px on all ten
shelves at 1024, 1200, 1440 and 1920**; below 1024 the pull computes to 0 and there was a 16px gap all along.
What he saw was the XS Energy can's silver top sitting on "BEFORE THE SESSION" — **pre-existing, and the dark
bay simply made it visible where the light one hid it**. `.rk-panel .bay-packs` now takes that 47.4px back as
`padding-top`, which puts the desktop gap at the phone's own **16px, with no overlap on any shelf at any
width**. The numbers are copied from the line above them; change both together, and re-measure on
`energy-focus`, whose can is the tallest pack on the rack.

**The open bay went dark first (2026-10-09).** Peter: *"when we open a plate, I think the background should be different
than the surrounding areas, they're both basically tan right now"* — then, shown four treatments, *"lets go b"*. It
was `color-mix(in srgb, var(--sand) 45%, var(--chalk))` standing on the chalk field: two tans a few percent apart, so
it read as the page with a border drawn on it rather than as a surface. `.rk-panel` is a deep teal gradient now
(`--teal` 94% to 86% toward black) with a sand hairline and a drop shadow; the copy inverts to chalk, the line under
the heading to `--on-dark`, "See all" and the load button to sand. **The plate-colour strip along the top edge and
the notch above it are untouched**, so the bay still belongs to the plate that opened it. **It is NOT glass and must
not become it** — there is no picture behind the rack to look through (see "The glass"), it is a flat dark fill, which
is also why its figures are computed rather than sampled: heading and pack names **13.39:1**, the line **9.65:1**,
"See all" **10.34:1**, the button's teal on sand **9.96:1**, all against the lighter gradient stop, verified live on
five bays at 390 and 1440. Focus rings inside it go sand, on the same line as `.dark` and the masthead — the global
ring is teal and would have been invisible. The three options not taken were near-white, a plate-colour tint on
near-white (the one that changes per bay) and a 28% tint on the tan, which turns every plate's colour to mud.

**The plate colours, rebuilt (2026-10-09).** Peter: *"shouldnt we add some more distincitive plate colors? like
yellow is a common one, but instead we have 2 versions of tan and 2 versions of brown and 2 versions of green."* He
was right, and the audit found worse than he could see. **The palette had only ever been held to two gates** — text
must read on a plate (`plate_ink()`, which exits the build) and no two plates may look like the same mark at chip
size — and **nothing ever asked the ten to be far apart**, so a set of muted earth tones passed both and the rack
came out tan. Measured on the old ten: **two pairs were under the 6 floor the code's own comment claimed** — Daily
Foundations vs Men's green at **3.2 under a protan eye** (that is Peter's "two greens": brown and green collapse
together) and Fat Loss vs Daily Foundations at **3.8** — six pairs were under 8, and only 2 of 10 plates carried any
real chroma. Three plates moved, and the reasoning is in the `PLATES` comment:
`energy-focus #E2C8AE -> #F0C505` (the yellow the rack was missing — real bumpers run red 25, blue 20, YELLOW 15,
green 10, white 5, and the rack is pretending to be competition bumpers), `fat-loss #8A543E -> #9D2C07` (a rust, out
of the brown cluster) and `daily-foundations #6B5646 -> #D9B081` (a warm wheat — the plate that broke the floor twice,
and **the fix has to be LIGHTNESS, not hue**: a protan or deutan eye loses the red-green axis, which is exactly where
brown and green differed). Result: **worst separation 3.2 -> 7.4, pairs under 6 two -> none, pairs under 8 six -> one,
worst flat contrast 6.14 -> 7.12, chroma above 30 two of ten -> five of ten.** **A third gate is now in force —
SPREAD** — so keep all three when a plate moves: flat contrast through `plate_ink`, >=6 (aim 8) separation under a
normal, deutan AND protan eye, and don't let the ten drift back into one muted band.

**Ink plates need a softer rim (`.is-light`, 2026-10-09).** A light plate carries its name in ink, and the rim's top
inner shade falls **exactly where the name sits** — so the one thing that gives a dark plate its margin takes it away
from a light one. Measured under the glyphs themselves: every white-text plate kept **0.62-1.02** of its flat ratio,
while the ink plates kept **0.39-0.72**, and the new yellow rendered at **4.09:1, under the floor**. The build now adds
`is-light` to a plate whose `plate_ink()` is not white, and `style.css` halves that plate's top shade (nothing else
about the rim changes, so it still reads as a moulded bumper). With it the yellow is **6.83** and **all ten clear 4.5:1,
worst 5.78** (Women's Health; Hydration 5.85, Everyday 5.95, Men's 6.02, Daily Foundations 6.26, Fat Loss 6.28,
Recovery 6.50, Energy & Focus 6.83, Skin Redefined 8.21, Protein 10.79) across 390/820/1440 at 1x and 2x. **This is
what lets the rack carry a saturated light plate at all** — do not drop it without re-measuring every plate.

**How to measure a plate, and the two traps.** Screenshot the rack twice, once normally and once with
`color:transparent` **and `text-shadow:none`** on `.rk-name`/`.rk-line`/`.rk-on` (the name is moulded with explicit
rgba shadows, so hiding the colour alone leaves them painting and you measure the letters against their own edge),
diff the two to get the glyph pixels, then read the hidden shot at exactly those pixels. **Trap one: never measure the
element's box.** A plate is a circle in a square box, so `.rk-line`'s rectangle runs off the disc at the bottom corners
and samples the page. **Trap two: scroll clear of the fixed chrome.** `--mh` plus `--pin` of masthead and pinned strip
sit over the top row, and measuring through them reported Hydration at 3.00:1 and had me tell Peter the live site was
broken. It was not — Hydration was 5.06 before today and is 5.85 now. The script is `scratchpad/rendered2.py`.

**A plate landing on the bar (2026-10-09).** Peter asked for an animation when a plate "pops onto the bar", and
for options 1 (slide onto the shaft) and 3 (the bar takes the weight). **Both were already built** — the find is
worth keeping, because the instinct on seeing nothing is to write a third one. A plate parks `(--n + --off)`
steps past the sleeve's outer end, where `.bb{overflow:clip visible}` cuts it off, and `.on` slides it in to its
own step over 360ms on `cubic-bezier(.22,1.2,.36,1.04)`, which overshoots at the stop: **48.6px of travel at 390
and 59.2px at 1440** — the whole visible length of the sleeve, and it reads. The bar's recoil in `paint()` did
not. Everything on a bar is drawn from its own font-size and the pinned strip sets that to **3.2px** (3.9 from
1024), so the flat `.24em` dip came to **0.76px at 390 and 0.92px at 1440** — under one device pixel at 1x, in
the code and never on the screen. It is `max(2.6px,.24em)` now, with a 0.9px rise after it and 420ms instead of
320: **measured live at 2.38px down and 0.83px up at both widths**, and it still scales up on "That's my stack",
whose bar runs to 15px type. The plate's opacity transition went 140ms → 70ms for the same reason: the clip is
what reveals the plate, so the fade only kept it half transparent for the first 40% of its slide. Reduced motion
skips the recoil whole (`!reduce.matches`, unchanged) and kills the slide's transition, as before. **A px floor,
not an em, is the lesson**: anything sized off `.bb`'s font-size disappears on the strip.

**The plate flies to the bar (`fly()` in `_script.html`, 2026-10-09).** What Peter actually meant: *"the entire
plate that we select moves from where we have it to our stack up above"* — the option I had argued against. He was
right to want it. A copy of the rack plate is flown, `position:fixed` on `<body>`, from where it stands to where it
will sit on the pinned strip, over **620ms**, shrinking and **turning edge-on to the strip plate's own 3-5px
sliver** — the rack draws a plate face on and the bar draws it side on, and the flight is the turn between them. The strip's
own plate is held back (`opacity:0`, `transition:none`) while the copy is in the air and revealed at **86%**, so the
two cross over instead of one blinking out before the other lands. Measured: **143px of travel at 390, 261px at
1440**, both monotonic, final width 3px and 5px against strip plates of 3.89px and 4.75px.
- **It is strictly an extra.** `fly()` returns false — and every caller falls back to the slide — when reduced
  motion is set, when the strip is not up, when the rack plate is off screen, or when the destination has no box.
  Verified: with the strip down the plate still lands, nothing is left hidden, no copy is left behind, no errors.
- **It is a real 3D turn, and the way it is built is the point** (Peter: *"does the plate turn as it goes? if it
  just floats up to the bar that may read kind of tacky"*). The first version narrowed it with `scaleX`, which held a
  circle for the first half and then squashed flat at the end — a squash, not a turn. **The two jobs are split across
  two elements**: `perspective` is a CSS PROPERTY on the wrapper, the wrapper animates translate + **uniform** scale
  so the disc stays a disc, and the cloned plate inside animates `rotateY` alone. Each keeps a single, same-shaped
  transform list and interpolates componentwise. Putting `perspective()` and `rotateY()` in ONE list with translate
  and scale is what made the earlier attempt decompose to a matrix and send the copy wandering sideways. The turn
  foreshortens — the hub and the lettering compress, the near edge reads larger — which `scaleX` can never do. The
  angle is **computed, not chosen**: `acos(dr.width / (sr.width * sy))`, capped at 86°, so the copy's width lands on
  the strip plate's own (83° at 390).
- **Two more things cost real time, so do not undo them.** The landing point carries **no scale term**:
  `transform-origin` is the centre, so scaling does not move the centre, and multiplying it in put the copy down in
  the wrong place. And the travel easing is **`cubic-bezier(.42,0,.58,1)`**; the first one tried,
  `cubic-bezier(.36,.02,.2,1)`, put the plate at the bar by 40% of the duration and left the rest of the flight empty.
- The destination's rect is read with its **transition suppressed**, or it is read a third of the way through its
  own slide. A real-time `setTimeout` tidies the copy away if the tab is backgrounded mid-flight — **stub
  `setTimeout` before stepping the animation by hand**, or that timer removes the copy while you are looking at it
  (it had me chasing a flight that appeared to vanish at 240ms). The bar's recoil and the newest-plate flash both
  wait for the landing when the flight runs.

**Section joins.** Two sections that met each laid a full `--sec` on the join, so every boundary was two of them.
`.sec + .sec,.sec + dialog + .sec{padding-top:calc(var(--sec) * .5)}` (`#story` is a `.sec` now) sits next to `.sec{padding:var(--sec) 0}`
and gives a join one full `--sec` and half the other. It applies to every page, so a new section added anywhere gets
it. `.hero + .sec` is deliberately left out.

## Build your goals: the first-time funnel on one route (2026-10-09)

Eric Elizes, relayed and approved by Peter: *"anything relevant to the first time experience would go
here. the entire funnel would live at this route... If you are running multiple ads, then you could have
multiple versions and A/B test per ad... Because the ENTIRE funnel is captured in this 'experience' rather
than spread out across different pages, you can easily hotswap and test different funnels dynamically."*
And: *"if someone isnt new also they can x out of it or smth."*

**The two halves are the site's own rack and its own call — `rack_section()` and `_consult.html` — not
copies.** The call was lifted out of `homepage.template.html` into **`site-src/_consult.html`** so one copy
can stand on two pages: it is a live form with its own validation, consent and thank-you, and a second
hand-written copy would drift and then mislead somebody. Its return URL is passed **per page**.

- **`FUNNELS` in `build_homepage.py` is the whole experiment.** Each row is `(suffix, key, order, headline,
  lead)`, and **the order of the two halves IS the variant**: `build-your-goals.html` is plates-then-call
  (today's funnel) and `build-your-goals-2.html` is call-then-plates. That pair is deliberate — Peter has
  been *"tempted to get rid of the weights / barbell altogether"* on a hunch, and this settles it with his
  own traffic. **Adding a variant is one row** and nothing else follows by hand.
- **`FUNNELS[0]` is canonical**: the only one indexed, the one every other variant points its canonical at,
  and what a visitor who types the route gets. The rest are `noindex`.
- **The coin flip lives in `index.html` and nowhere else** (hand-written, copied verbatim into `plus/`).
  First visit → a variant; after that → the shop. **The `<meta refresh>` below it is the fallback and must
  stay**: no script, blocked storage, or anything throwing, and the visitor goes to the shop as always
  (verified with script disabled). `location.replace` keeps it out of the back button. **The build checks
  the page names in `index.html` against `FUNNELS`** and stops if they have drifted.
- **The funnel page records itself**, not `index.html`: `data-funnel` carries the key, the page writes
  `aspire-seen` and `aspire-funnel`, and fires `ftue_shown{funnel}`. Landing from an ad counts the same as
  being routed. **`track()` then puts `funnel` on EVERY event**, so the whole funnel reads per variant in
  PostHog without a second set of event names. The way out (`data-funnel-out`) marks them seen and fires
  `ftue_skipped`.
- **`plus_links()`'s page list is now derived from the constants, not typed out.** It was a hand-kept list,
  and both pages added this day were missing from it — so the copy's funnel form carried an absolute
  `_next` back to the **plain** site, which would have walked a plus visitor out of the copy on a no-script
  send. **A new page is a new constant; add it there.** Verified: every `plus/` page now returns into
  `plus/`.
- **Never write a placeholder's own braces in a comment inside a partial.** A partial is substituted into a
  page and the unfilled-placeholder check then runs over the result, so a token named in prose comes back
  as an unfilled one and stops the build. It did, in `_consult.html`'s own header.
- Verified: a 20,000-draw flip is 10,036/9,964; a returning visitor reaches the shop; the skip link marks
  them seen and goes to the shop; both variants carry both halves in their own order with the right
  canonical and noindex; the call's action and return URL are right on all four pages; no console errors
  on either copy; 2,602 local references across 36 pages with none missing; the guard still clean; and the
  funnel head measures **6.04:1** at 390 and 1440 under the glyphs.

## A product's backdrop is its OWN colour (`pack_tint`, 2026-10-09)

Peter: *"we should make the background colors for each prodct match the style. for instance, createine is
whtie and black so the background is more white, strawberry grass few whey is more pink, choco pb bars is
more browns etc."* It **replaced the shelf's plate colour**, which tied a card to the rack but meant two
products from one shelf sat on the same field and said nothing about the pack.

- The colour is **read off the product's own photograph**. `assets/products/*.webp` are real cut-outs with
  an alpha channel, so only pixels at **alpha > 200** are read and the background cannot pollute it.
- The mean is **weighted by saturation** (`0.18 + s`), because a pack is mostly white card and its brand
  colour has to win *without* dragging a genuinely neutral pack off grey. Creatine comes out `#A6A4A4`,
  the raspberry twist tubes `#EE989B`, Energy + Focus `#47BF82` — exactly the three cases Peter named.
  Lightness is clamped to .36–.84 so nothing is a hole or a blank, and `style.css` mixes it well back
  toward the hollow: **this is a direction, not the colour the field ends up.**
- **Cached in `assets/.tints.json`** against each file's mtime and `TINT_VERSION`, or the build would turn
  from 0.05s into seconds of reading 105 photographs (measured: 0.81s cold, 0.32s warm). **Bump
  `TINT_VERSION` when the maths changes.**
- The Start here lead counts `FEATURED` rather than naming a number: it said "Eight" while the list had
  nine.

## What stacks with what (`STACKS_WITH`, 2026-10-09)

Peter, choosing the Start here eight: *"raspberry twist tubes (maybe theres a way to autorecommend those
with the creatine since they stack nicely together)"*. The product card now carries one quiet line under
the facts: **"Stacks well with <product>"**.

- **It is a CURATION, not a rule engine.** Nothing is inferred from shelves or families, because a wrong
  pairing on a product card is Peter recommending something he did not. **Both directions are written
  out** and the build exits if a pair does not point back, or if either name is not in `share-links.csv`.
- It is **never called a bundle** and it **never says what the pair does together**, which would be a
  claim. One pair today: `XS Creatine+` ↔ `XS Sports Twist Tubes - Raspberry Lemonade`.
- With script, the line opens the partner's own card when that product is on the page, and otherwise
  links to the shop with it searched. **The reopen waits for the dialog's own `close` event, not a timer**:
  `close()` plays a flight back to the tile first and `open()` refuses while `dlg.open` is still true, so a
  260ms delay lost that race and the card simply shut (measured). A product with no pair shows nothing.

## A third tab: Start here (2026-10-09)

Peter, after Eric Elizes called the current home *"a normal general store"*: *"I'm wondering if that means
really we want a third tab with products demonstrated a little more cleanly. For example, if you look at
this website, I only have six products up, but they look really clean."* (aspirehealth.pro.) **The Shop tab
is still the whole catalogue and stays that way; `start.html` is the handful, with air around them.**

- **It shows `FEATURED` and nothing else.** **One curation, one place**: do not invent a second list
  beside it. **Peter chose the eight himself on 2026-10-09** — Elite Peach Mango, Creatine+, GI Primer,
  the chocolate peanut butter bars, Sleep Health, the raspberry twist tubes, the men's daily multivitamin
  and XS Energy + Focus — replacing a set that had been picked for photographic uniformity. **That
  uniformity is the cost**: the old eight were all props-free studio shots "so the grid reads as one
  series", and only four of his have one in `product-shots/`; the rest fall back to catalogue images, so
  the row is less even. **The fix is four more studio shots, not a different eight.** Two of his names
  were ambiguous and are resolved in the table's comment. Note also that the backdrops are shelf colours,
  so two products from one shelf sit on the same colour — correct, but it means the row is not eight
  different colours.
- Each card carries `card_data()` and keeps the `card-link` class, because `_script.html`'s tile selector is
  `a.card-link[data-name]` — so **the same product card opens from here as from anywhere else**, and its
  backdrop takes the same `--tint`. "Ask for a free sample" routes by the shop tab's `?try=`, as a shelf
  page's does. **No prices**: the site has never carried one, Amway owns them and they move.
- **Every word sits BELOW the colour field, on the chalk**, so nothing is ever read off a colour that
  changes per product. Measured under the glyphs: worst **5.79:1** at 390, **5.88:1** at 1440.
- `.sc-link` is a **flex column, not a grid**: cards in a row stretch to the tallest, and with a grid the
  extra height landed on the art panel, so a 1:1 field became a taller one and that card's words started
  lower than its neighbours'. `margin-top:auto` on `.sc-go` puts the slack at the bottom instead.
- `.sc-art .shot` needs **`min-height:0`**: the shot carries `aspect-ratio:1` of its own (`.shot-studio`),
  and a grid item's automatic minimum size refuses to go below its content, so the panel came out 16px
  taller than its own ratio asked — and only on the cards whose shot is a studio one.

**The tab bar is three wide now, and that cost two measured fixes** — re-measure both if a tab is ever
added, removed or renamed:
- `.tabs` is `repeat(3,1fr)`, not `1fr 1fr`. The third tab simply **wrapped onto a second row** that the
  fixed `--tabh` had no room for. Below 480 and below 360 the labels step down so "Our approach" still fits
  a third of a 320px window on one line. Verified one row, no clipping, no sideways scroll, 320 to 1023.
- The wordmark's name is hidden again through **1279** (it was 1024-1099). The extra tab costs the pill
  about what "Products" cost the nav before it went, and **at 1100 "Book a free call" ran straight over the
  search field** — measured, and plain in a screenshot. Verified afterwards: zero collisions and a clean
  24px gap at 1024-1920 (11px at 1024, where the search sits at its 138px floor, as before).
- **The Shop's first screen did not move**: "Pick your goal" still ends at **654 of 844 at 390 and 576 of
  640 at 320**, to the pixel, because the bar is three columns of the same 40px row.

The label "Start here" and the page's copy are **DRAFT** and Peter's to rename.

## The product card's backdrop changes with the product (2026-10-09)

Peter, on aspirehealth.pro: *"one thing I really like about the products on that website as well is that
when you click them, it shows like a back drop that changes. That part's pretty cool. And it, again, it
reads high-end, professional, quality, good pictures, good shots. Not crammed."*

`#pcard`'s art panel now takes **the product's own shelf plate colour**. The build puts `data-tint` on every
pack and tile from `PLATES[cat_of[product]]` — read, never written by hand, **so a plate that moves takes its
cards with it** — `_script.html` copies it onto the dialog as `--tint` on open, and `style.css` mixes it back
toward the hollow (16% / 30%). A product on no shelf clears the tint and the panel keeps the plain hollow it
always had. **Nothing is written on that panel**, so there is no contrast to hold here, only a pack to light.
Protein's near-black gives a graphite field, Daily Foundations' wheat a warm sand, Energy & Focus' yellow a
soft lemon, Recovery's indigo a pale lavender — which is the whole point: it ties the card to the rack.

## The goal question is not asked twice (2026-10-09)

Eric Elizes: *"build your barbell asks you what your goals are effectively, then booking flow re-asks in
step 1... I think it might be more straightforward having 1 cohesive narrative, such as 1. Pick your plates
(this is where you would pick your goals)."* Peter: *"yeah lets kill the duplicate goal question."*

**The site itself calls the shelves goals** — the hero's button is "Pick your goal", the rack's heading is
"What are we maximizing?", the fact row counts "10 goals" — so a visitor who loaded plates and then met five
differently-worded goal chips was being asked the same thing in a second vocabulary.

- **When anything is on the bar, the goal step is not built at all**: the card is two steps, the counter and
  the pips follow, and the first question is the training one. A cold arrival who never touched the rack
  still gets all three. Without script every step is on screen as one form, which is right — nothing can
  know their stack.
- **NOTHING IS INFERRED, and that is the important part.** Ten shelves do not map onto five chips, and
  guessing one would put a goal the visitor never said onto Peter's call sheet. What goes out is exactly
  what they did: `goal` becomes the shelf names ("Protein, Hydration"), or the chip value if the macro
  calculator filled it, which still takes priority. The summary line reads "Fifteen minutes on protein and
  hydration."
- **The steps are keyed on `data-q` (`goal` / `training` / `you`), not on their index**, because one of them
  may not be there. `cAsk` switches on the name. Any new step needs a `data-q` and a branch.
- The stack is read straight from `localStorage` and `#lbpin`'s `data-plates`, **not from `LB`**, which is
  defined further down `_script.html` and is still null when the consult block runs. The approach tab has no
  rack and no grid, so the stack cannot change under the form: it is decided once, at load.
- A step index saved under the old three-step card clamps safely (`cGap()`), verified.

## No Calendly: the call form asks for a phone number (2026-10-09)

Peter: *"let's drop the Calendly. Here's why. They can give me their phone number. I can always call them or
text them to book a time manually. And that's fine... And if I want to build back in the Calendly later, I
totally can."* It came out of Eric Elizes' note that a number is less friction than a booking flow and lets
Peter text. He also chose the shape: **"one form one voice fewer steps"** — so the call card did not merely
bolt a phone field on, it took the free sample's own posture, which already had this right.

- **`#consult-form` posts to FormSubmit now**, exactly as `#sample-form` does: same service, same JSON shape,
  same failure wording, same honeypot. `CONSULT_TO = SAMPLE_TO` — **one hash is one email address**, and the
  two forms are told apart by `_subject` ("Call request · Aspire Health"). A second hash would mean a second
  confirmation email for Peter to click and nothing gained. `CONSULT_ACTION` / `CONSULT_ENDPOINT` /
  `CONSULT_NEXT` sit beside the sample's four.
- **Still three steps** (Eric's "minimize clicks"): the five goals, Peter's six training answers, then the last
  one, which gained **name and phone, both required**, above the two blanks it already had.
- **The consent tick is required and is not decoration.** Peter is going to ring or text a number somebody
  typed in. It is worded and shaped like the sample's, with the same optional "keep in touch" beside it, and
  the same privacy line under the button. **Do not quietly drop it.**
- **`cform.noValidate = true` is load-bearing.** The last step's required fields sit in a HIDDEN fieldset until
  the visitor reaches it, and Chrome silently refuses to submit a form with an invalid control it cannot focus
  — with native validation left on, the card simply stopped responding to its own button (measured, and it cost
  real time to find). No-JS keeps native validation, because without the script every step is on screen.
- **`if(cSync)cSync()` runs right before the body is built**, and was briefly lost in this change: it writes the
  calculator's macros and the bar's "Interested in: …" into the note. Without it Peter gets the note with
  neither. Verified in the captured payload.
- The thank-you is `#call-sent`, on the sample's own `.s-done` / `:target` machinery, plus
  `.consult-dusk:has(.s-done:target) #consult-form{display:none}` for the no-script return.
- **What the sample lent this card had to be re-lit.** The consent ticks, the "what happens next" list, the
  privacy line and the send's error were written for the LIGHT sample card and arrived set in `--ink`/`--text`
  — invisible on the teal glass. They are inverted in the `.consult-dusk #consult-form` block. Measured under
  the glyphs: **worst 9.38:1** at 390 and 1440. **Measuring their BOXES gives a false failure** (1.29 and 2.11)
  because the checkbox and the numbered badges sit inside the text's bounding box — the same trap as the plates.
- **Gone with it:** `CONSULT_URL`, the Calendly `widget.js` loader (`withCalendly`), the `a[data-quick]` popup
  handler, the `widget.css` link and `#consult-embed` / `.c-embed`. **That was the only third-party script the
  site ever loaded on a tap.** `CONSULT_QUICK_URL` and `quick_call()` remain, rendering a plain link, so a
  quick-call route can return without the widget returning with it. Putting Calendly back is those constants
  plus the loader, which is why it was all kept in one place.
- Verified: three steps advance; each required field reports its own message in turn; a failed send keeps every
  typed answer and restores the button; a successful send (fetch stubbed — **never submit the live form**)
  hides the form, shows the thank-you and clears `aspire-consult`; the no-script `:target` return shows the
  thank-you with all three steps open; no console errors on any page of either copy; and `#how`, the pinned
  bar and the header nav all still point at `#consult`.

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

## Analytics: PostHog (2026-10-09)

Peter: *"can we add in posthog?"*, with `npx -y @posthog/wizard@latest`. **The wizard was not used and should
not be**: it is built for npm framework projects, and this repo has no `package.json`, its whole build is one
Python script, and anything it wrote into a generated page would be gone on the next build. It also needs a
PERSONAL key (`phx_...`) or a browser login to Peter's own PostHog account, which is his to give, not mine.

Analytics goes through the build like everything else: **`{{ANALYTICS}}`**, in `shared`, filled into the head of
every page of **both** published copies at once. The two report to the same project and are told apart by path
(`/RAW/` and `/RAW/plus/`). `index.html` is hand-written and carries nothing, which is right — it redirects at once.

- **`site-src/_posthog.js`** is PostHog's own current loader, copied from their docs and **not edited**. When they
  publish a new one, replace that file wholesale. It is read by `part()` like every other partial.
- **`POSTHOG_KEY`** is the **project** token (`phc_...`): public by design, and it belongs in the page source. A
  **personal** key (`phx_...`) is a secret and must never be in this repo or in a page — `analytics()` **exits the
  build** if it is handed one (verified). **Peter's token went in on 2026-10-09 and it is LIVE**: all 28 pages (14
  at the root, 14 under `plus/`) carry it. A public project token means anyone can post events to the project —
  that is inherent to client-side analytics, and the answer is PostHog's own authorized-URLs setting, not hiding
  the token. Emptying the constant switches the whole thing off again and restores the output byte for byte.
- **`POSTHOG_HOST`** is the only place a region is named; the loader derives the assets host itself
  (`.i.` → `-assets.i.`). **`POSTHOG_REPLAY = False`**: session replay records the visitor's screen, and the
  free-sample form on the Shop is LIVE and takes a visitor's name and what they are after. The snippet writes
  `disable_session_recording` explicitly rather than leaving it to the project's own setting, so the page cannot
  start recording because a toggle moved somewhere else. Turning it on is Peter's call.
- **Never on a demo export** (`if DEMO`): a preview must not report itself as the live site.
- Verified with the real token on `shop.html`, `homepage.html`, `about.html`, `bloodwork.html` and both of the
  `plus/` copies: the loader tag is inserted, `init` queues with the right token, `api_host` and
  `disable_session_recording:true`, the snippet sits inside `<head>`, and the page still works. **Always test with
  `*.posthog.com` mapped to 127.0.0.1 in Chrome's resolver** — otherwise every local run posts localhost events
  into Peter's real project. The first genuine events are the ones from the live site after a push.
- **The funnel is instrumented (2026-10-09)**, which is Eric Elizes' first recommendation and the one Peter
  asked us to act on: *"track conversion rate in whatever your funnel is."* Autocapture only knows "a button
  with this text was clicked"; these are the named steps of Peter's own funnel, at the end of `_script.html`:
  `shelf_opened{shelf}` → `plate_loaded{shelf,product,plates}` → `product_viewed{product,from}` →
  **`amway_opened{product,from}`**, plus `sample_submitted`, `call_submitted` and `page_kind{page,plus}`.
  `from` is one of product_card / shelf_bay / all_products / my_stack / other.
  - **`amway_opened` runs in the BUBBLE phase and skips a prevented click, on purpose.** A pack in a bay and
    a tile in the grid are both `<a href="amway.com/share-link/…">`, but with script the site cancels those
    clicks and opens the product card instead — the first version counted them and reported an exit to Amway
    every time somebody merely looked at a product. Measured after the fix: one real exit, one `amway_opened`.
    What is left is the card's own "Buy on Amway" and, with no script, the raw links. **Do not move this
    listener to the capture phase.**
  - **No personal data, ever.** Shelf and catalogue names only. The forms report THAT they were sent, not what
    was in them — verified by filling a name and a phone into the sample form and checking the payload.
  - `track()` is a no-op when PostHog is absent, so a blocked, offline or key-less build is unaffected.
  - Names are stable: renaming one orphans the funnel already built on it in PostHog.
- **Session replay is ON** (`POSTHOG_REPLAY = True`, 2026-10-09). It was off; Eric recommended replay and
  heatmaps by name and Peter said to follow him. PostHog masks typed input by default — if that ever needs to
  be certain for the live sample form, set the masking explicitly rather than trusting the default.
- **Not done, and Peter's to decide:** there is no consent banner on the site. PostHog sets a cookie and
  autocapture records clicks and the text of what was clicked (not what is typed into a field). For US traffic
  that is normally fine; EU visitors are a different question. Raise it with him rather than adding a banner.

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
