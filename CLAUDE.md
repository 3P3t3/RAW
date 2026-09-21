# Aspire Health — static site, built by one Python script

## Team: who works where, and who pushes

Several Claude sessions work on this site at once, each in its own git worktree on its own branch:

| Session | Folder | Branch |
|---|---|---|
| RAW 0: EM | `~/Desktop/Raw` | `main` — the live site |
| RAW 1: General | `~/Desktop/Raw-worktrees/raw` | `raw/work` |
| RAW 2: Backgrounds | `~/Desktop/Raw-worktrees/raw2-fizz` | `prototype/fizz-and-wipe` |
| RAW 3: Logos | `~/Desktop/Raw-worktrees/logo` | `logo/design` |

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
  `FEATURED`, `GOAL_TILES`, `FINDER`, `ISLANDS`, `CAROUSELS` tables
- `site-src/homepage.template.html`, `site-src/category.template.html`
- `site-src/_header.html`, `_footer.html`, `_dialogs.html`, `_icons.html`, `_script.html`
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

`index.html` is a hand-written redirect to `homepage.html` and is not generated.

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
