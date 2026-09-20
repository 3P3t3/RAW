# Aspire Health — static site, built by one Python script

## Never read the generated pages

`homepage.html` is ~106k chars (~26k tokens). All eight generated pages together are ~600k
chars (~150k tokens). All nine files in `site-src/` together are ~89k chars (~22k tokens).

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
- `site-src/style.css` — inlined into every page via `{{STYLE}}`; there is no served .css
- `share-links.csv` (`product,share_link,photo`) — the product list, 65 rows
- `bestsellers.csv` (`product,units_this_week`) — top 3 rows become the podium; `product` must
  match a `share-links.csv` name or the build exits. Blank `units_this_week` just hides the count.

Generated (never hand-edit; the next build overwrites them):
- `homepage.html`
- `category-daily-foundations.html`, `-energy-focus.html`, `-fat-loss.html`, `-hydration.html`,
  `-protein.html`, `-recovery.html`, `-skin-redefined.html`
- `assets/products/`, `assets/cutouts/`, `assets/.cut-version`

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
