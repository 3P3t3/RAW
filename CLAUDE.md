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

`homepage.html` is ~77k chars (~19k tokens). All eight generated pages together are ~370k
chars (~93k tokens). All nine files in `site-src/` together are ~89k chars (~22k tokens).

**Reading one generated page costs more than reading the entire source of the site.**
To check something in a generated page, grep it:

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
- `share-links.csv` (`product,share_link,photo`) — the product list, 65 rows
- `bestsellers.csv` (`product,units_this_week`) — top 3 rows become the podium; `product` must
  match a `share-links.csv` name or the build exits. Blank `units_this_week` just hides the count.

Generated (never hand-edit; the next build overwrites them):
- `homepage.html`
- `category-daily-foundations.html`, `-energy-focus.html`, `-fat-loss.html`, `-hydration.html`,
  `-protein.html`, `-recovery.html`, `-skin-redefined.html`
- `style.css`, `assets/products/`, `assets/cutouts/`, `assets/.cut-version`

`docs/macro-calculator.md` records the homepage macro calculator: where the maths came from, every
formula and rounding in `mcCalc` in `_script.html`, and worked examples. Read it before touching them.

`index.html` is a hand-written redirect to `homepage.html` and is not generated.

`assets/wave-horizon.webp` is the footer's horizon: Peter's lit wave, cropped to the wave band
alone (his artwork carries the lockup type under it, which must never reach the page). It is
placed by hand, not generated, so the build never rewrites it and nothing cleans it up.

`assets/peter/` holds Peter's photos for the consult section: `family-320.webp` (Peter, his wife and
daughter) and his before/after composites `front-`, `side-`, `back-` at `640.webp` and `960.webp`.
They are cut from his originals in `~/Desktop/aspiree/assets/rooms/` and placed by hand, so the
build never touches them. Peter chose to make them public; the repo is public because Pages
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

## Build

    python3 site-src/build_homepage.py     # from the repo root

Takes ~0.05s and prints `65 products (65 with photos)` plus the per-category counts. Run it after
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
