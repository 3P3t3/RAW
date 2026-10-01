"""Build homepage.html from share-links.csv + product-photos/.

Run from the project folder:  python3 site-src/build_homepage.py
Edit share-links.csv (product, share_link, photo) and re-run to update the site.

One run writes the site TWICE: the plain site at the repo root, and the copy that offers Peter's
CCRX route under PLUS_DIR/ (both are published, from one push). See "the CCRX copy" below for the
switch, the guard that keeps the CCRX link out of the plain copy, and --ccrx / --no-plus.
"""
import csv, hashlib, html, inspect, os, re, shutil, sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'site-src', 'homepage.template.html')
OUT = os.path.join(ROOT, 'homepage.html')
PHOTOS = os.path.join(ROOT, 'product-photos')
STUDIO = os.path.join(ROOT, 'product-shots')  # re-lit studio versions, already framed to one scale
ASSETS = os.path.join(ROOT, 'assets', 'products')
CUTS = os.path.join(ROOT, 'assets', 'cutouts')  # transparent versions, for products shown on dark bands
STAMP = os.path.join(ROOT, 'assets', '.cut-version')  # fingerprint of normalize(), written once a build finishes
# one shared stylesheet, linked by every page; it sits beside the pages rather than under assets/ so its
# url(assets/...) backgrounds resolve against the same folder they did when the css was inlined
STYLE_OUT = os.path.join(ROOT, 'style.css')
RECUT = False  # set for the whole run when that fingerprint moved, so every cached cut-out counts as stale
# `--demo OUTDIR` exports a public copy of the site and writes nothing else: OUTDIR/homepage-demo.html and
# every shelf page as OUTDIR/category-<slug>-demo.html, all linked to their own OUTDIR/style-demo.css, so the
# live pages and their shared style.css are never touched. Each is noindexed, its canonical and og:url name
# its own demo address, and every link to the homepage or a shelf inside them names the demo copy instead
# (demo_links), so a visitor never falls out of the demo into the live site. It photographs nothing (no
# cut-outs, no copies), so run a normal build first; it then lists what it links that main lacks.
DEMO = None
DEMO_SUFFIX = '-demo'
DEMO_PAGE = 'homepage-demo.html'
DEMO_STYLE = 'style-demo.css'
# `--demo OUTDIR --demo-name NAME` exports a second demo beside the first, as OUTDIR/homepage-demo-NAME.html,
# OUTDIR/category-<slug>-demo-NAME.html + style-demo-NAME.css, with their own canonical, og:url and sample
# _next. `--view VIEW` builds with that SHELF_VIEW instead of the one below (e.g. `--demo OUTDIR --view case`
# for the case demo from this branch).

# ---- the CCRX copy: one source, two published sites -----------------------------------------
# Peter has a second, paid-referral business: CCRX (prescription compounded peptides and an
# at-home blood panel, fulfilled by Avellum Health). He wants one site he can send to anyone and
# one that also offers that route -- without a fork, because two copies drift and then leak. So
# every build writes the site TWICE from this one source:
#   the plain site  ->  the repo root   https://3p3t3.github.io/RAW/homepage.html
#   the CCRX copy   ->  PLUS_DIR/       https://3p3t3.github.io/RAW/plus/homepage.html
# CCRX below is the switch, and the link it carries is the ONLY difference between the two.
# Peter, 2026-10-01, verbatim: "It's not a big deal if some peptide verbiage leaks into the
# regular website. In fact, at some point, I probably will do that. The only thing to avoid is
# having the specific uh, crystal clear RX website built into the other website. ... Just the
# link itself." So words are free in both copies; the LINK is what the switch turns on and what
# guard() refuses to let into the plain copy, whatever anyone edits.
CCRX = False      # OFF for the plain site. The build's second pass turns it on; --ccrx on|off overrides it
CCRX_URL = 'https://ccrx.health/n/HERSCHELMAN'     # Peter's referral link (his own, attribution included)
CCRX_HOSTS = ('ccrx.health', 'avellumhealth.com')  # every host that link reaches; guard() bans all of them
                                                   # from the plain copy. The WORDS "CCRX" and "Avellum
                                                   # Health" are fine there (the footer already says one)
PLUS_DIR = 'plus'  # the folder the CCRX copy builds into. Peter has not named it yet: rename it here
                   # (and in the one .gitattributes line) and the whole copy moves with it
PLUS = False       # set for the build's second pass, the one that writes PLUS_DIR/
PLUS_BUILD = True  # write the copy at all; --no-plus skips it and leaves the plain site exactly as it is
PLAIN_WRITTEN = []  # the plain files this build wrote, each one already past guard()

# family prefix -> (type descriptor, goals, format). Longest prefix wins.
# Goals: R Recovery, L Lean Mass, E Endurance, S Sleep & Longevity (first = primary).
FAMILIES = {
    'Artistry Skin Nutrition Renewing Softening Toner': ('Skincare · Toner', '', 'topical'),
    'Artistry Skin Nutrition Sleeping Mask': ('Skincare · Overnight mask', 'S', 'topical'),
    'Artistry Studio Glow Boss Cleanser + Exfoliator': ('Skincare · Cleanser + exfoliator', '', 'topical'),
    'Nutrilite Balance Within Probiotic': ('Daily probiotic', 'S', 'powder'),
    'Nutrilite Begin Daily GI Primer': ('Daily digestive powder', 'S', 'powder'),
    'Nutrilite Magnesium': ('Mineral supplement', 'SR', 'pills'),
    'Nutrilite Organics All-in-One Bars': ('Organic nutrition bar', 'L', 'ready'),
    'Nutrilite Organics Ashwagandha Capsules': ('Organic herbal capsules', 'S', 'pills'),
    'Nutrilite Organics Chamomile Tea': ('Organic herbal tea', 'S', 'ready'),
    'Nutrilite Sleep Health': ('Nightly supplement', 'S', 'pills'),
    'Nutrilite Twist Tubes 2GO': ('Drink mix tubes', 'E', 'powder'),
    'XS CBD Cream': ('Topical cream', 'R', 'topical'),
    'XS CBD Pro Cream': ('Topical cream', 'R', 'topical'),
    'XS CocoWater Hydration Drink Mix': ('Hydration mix', 'ER', 'powder'),
    'XS Creatine+': ('Creatine powder', 'L', 'powder'),
    'XS Elite + Focus Energy Drink': ('Energy drink', 'E', 'ready'),
    'XS Energy + Burn 12 oz': ('Energy drink · 12 oz', 'E', 'ready'),
    'XS Energy + Focus Dietary Supplement': ('Energy tablets', 'E', 'pills'),
    'XS Energy Drink 12 oz': ('Energy drink · 12 oz', 'E', 'ready'),
    'XS Grass-Fed Whey Protein': ('Protein powder', 'LR', 'powder'),
    'XS Grass-Fed Whey Protein Powder Sachets': ('Protein sachets', 'LR', 'powder'),
    'XS Ignite Powder': ('Energy powder', 'E', 'powder'),
    'XS Juiced and Burn 12 oz': ('Energy drink · 12 oz', 'E', 'ready'),
    'XS Muscle Multiplier': ('Training drink mix', 'RL', 'powder'),
    'XS Post-Workout Recovery': ('Recovery mix', 'RL', 'powder'),
    'XS Pre-Workout Boost': ('Pre-workout mix', 'EL', 'powder'),
    'XS Protein Crisps': ('Protein snack', 'L', 'ready'),
    'XS Sparkling Juiced Energy 12 oz': ('Sparkling energy drink · 12 oz', 'E', 'ready'),
    'XS Sports Protein Bars': ('Protein bar', 'L', 'ready'),
    'XS Sports Protein Shakes': ('Protein shake', 'LR', 'ready'),
    'XS Sports Twist Tubes': ('Drink mix tubes', 'E', 'powder'),
    'n* by Nutrilite Sweet Dreams': ('Sleep gummies', 'S', 'pills'),
    # added 2026-09-27 from Peter's 43 new share links (the descriptors read off each pack's own label)
    'Fitness Jump Start Solution': ('XS training bundle', 'LR', 'powder'),
    'Nutrilite Advanced Omega': ('Omega softgels', 'S', 'pills'),
    'Nutrilite Cal Mag D': ('Calcium & magnesium tablets', 'S', 'pills'),
    'Nutrilite Carb Blocker': ('Mealtime tablets', 'L', 'pills'),
    'Nutrilite Concentrated Fruits and Vegetables': ('Fruit & vegetable tablets', 'S', 'pills'),
    "Nutrilite Men's Daily Multivitamin Tablets": ('Multivitamin tablets', 'S', 'pills'),
    "Nutrilite Women's Daily Multivitamin Tablets": ('Multivitamin tablets', 'S', 'pills'),
    'Nutrilite Complete Menopause Support': ('Once-daily tablets', 'S', 'pills'),
    'Nutrilite Iron Folic': ('Iron & folic acid tablets', 'S', 'pills'),
    'Nutrilite Prostate Health': ('Saw palmetto softgels', 'S', 'pills'),
    'Nutrilite Organics Horny Goat Weed & Tribulus Capsules': ('Organic herbal capsules', 'S', 'pills'),
    'Nutrilite Double X Multivitamin': ('Multivitamin tablets', 'S', 'pills'),
    'Nutrilite Hair, Skin & Nail Health': ('Biotin & collagen tablets', '', 'pills'),
    'Nutrilite Immunity Defense Zinc + Holy Basil': ('Zinc & holy basil tablets', 'S', 'pills'),
    'Nutrilite Joint Health': ('Glucosamine tablets', 'R', 'pills'),
    'Nutrilite Lean Muscle': ('CLA softgels', 'L', 'pills'),
    "Nutrilite Men's Pack": ('Daily supplement packets', 'S', 'pills'),
    'Nutrilite Memory Builder Supplement': ('Cistanche tablets', 'E', 'pills'),
    "Nutrilite Organics Men's Daily Multi Gummies": ('Organic multivitamin gummies', 'S', 'pills'),
    "Nutrilite Organics Women's Daily Multi Gummies": ('Organic multivitamin gummies', 'S', 'pills'),
    'Nutrilite Organics Ginger Mint Tea': ('Organic herbal tea', 'S', 'ready'),
    "Nutrilite Organics Lion's Mane Mushroom Capsules": ('Organic mushroom capsules', 'E', 'pills'),
    'Nutrilite Organics Turmeric Gummies': ('Organic turmeric gummies', 'R', 'pills'),
    'Nutrilite Perfect Pack': ('Daily supplement packets', 'S', 'pills'),
    'Nutrilite Prebiotic Fiber': ('Fiber stick packs', 'S', 'powder'),
    'Nutrilite Slimmetry Dietary Supplement': ('Supplement tablets', 'L', 'pills'),
    'Nutrilite Stress Relief Probiotic': ('Probiotic capsules', 'S', 'pills'),
    'Nutrilite Ultra Focus Energy Pack': ('Daily supplement packets', 'E', 'pills'),
    'Nutrilite Vitamin C Extended Release': ('Vitamin C tablets', 'S', 'pills'),
    "Nutrilite Women's Pack": ('Daily supplement packets', 'S', 'pills'),
    'Peak Performance Stack': ('XS training bundle', 'LR', 'powder'),
    'n* by Nutrilite Go Shield': ('Elderberry gummies', 'S', 'pills'),
    # added 2026-10-01 with the Everyday Health shelf: the four Peter parked when none of the nine fitted.
    # Each descriptor is the format and how often, off the pack's own label (as Menopause Support's is),
    # never what the name suggests it does. CoQ10 is the one ingredient any of the four names in legible
    # type; the herbs in their photos are pictures, not words, so none of them is named here.
    'Nutrilite Cholesterol Health': ('Once-daily softgels', 'S', 'pills'),
    'Nutrilite Liver Support': ('Twice-daily tablets', 'S', 'pills'),
    'Nutrilite Heart Health CoQ10': ('CoQ10 softgels', 'S', 'pills'),
    'Nutrilite Cellular Aging Support': ('Twice-daily capsules', 'S', 'pills'),
}

# Category pages: slug, name, tagline, heading, family prefixes that belong to it.
# A family may sit on more than one shelf: each shelf page lists everything its own list names.
# Its card tag (and its data-cat) names one home shelf, the later of them in this list.
CATEGORIES = [
    ('recovery', 'Recovery', 'Wind down, repair and sleep: post-workout mixes, magnesium, herbals and topical creams.', 'Everything in Recovery', [
        'XS Post-Workout Recovery', 'XS Muscle Multiplier', 'XS CBD Cream', 'XS CBD Pro Cream',
        'Nutrilite Magnesium', 'Nutrilite Organics Ashwagandha Capsules', 'Nutrilite Organics Chamomile Tea',
        'Nutrilite Sleep Health', 'n* by Nutrilite Sweet Dreams',
        'Nutrilite Joint Health', 'Nutrilite Organics Turmeric Gummies', 'Nutrilite Stress Relief Probiotic',
        'Peak Performance Stack']),
    ('hydration', 'Hydration', 'Electrolytes and drink mixes for long, hot and sweaty sessions.', 'Everything in Hydration', [
        'XS Sports Twist Tubes', 'Nutrilite Twist Tubes 2GO', 'XS CocoWater Hydration Drink Mix',
        'XS Creatine+']),  # also on Daily Foundations: it is half of Peter's hydration stack
    ('energy-focus', 'Energy &amp; Focus', 'Pre-workout, tablets and the full XS energy range.', 'Everything in Energy &amp; Focus', [
        'XS Pre-Workout Boost', 'XS Energy + Focus Dietary Supplement', 'XS Energy Drink 12 oz',
        'XS Energy + Burn 12 oz', 'XS Juiced and Burn 12 oz', 'XS Sparkling Juiced Energy 12 oz',
        'XS Elite + Focus Energy Drink',
        'Nutrilite Ultra Focus Energy Pack', 'Nutrilite Memory Builder Supplement',
        "Nutrilite Organics Lion's Mane Mushroom Capsules"]),
    ('protein', 'Protein', 'Powders, shakes, bars and crisps to hit your protein for the day.', 'Everything in Protein', [
        'XS Grass-Fed Whey Protein', 'XS Grass-Fed Whey Protein Powder Sachets', 'XS Sports Protein Bars',
        'XS Sports Protein Shakes', 'XS Protein Crisps', 'Nutrilite Organics All-in-One Bars',
        'Fitness Jump Start Solution']),  # a bundle built round a pouch of grass-fed whey, in its flavor
    ('fat-loss', 'Fat Loss', 'Powders, tablets and softgels to pair with your training.', 'Everything in Fat Loss', [
        'XS Ignite Powder', 'Nutrilite Carb Blocker', 'Nutrilite Slimmetry Dietary Supplement',
        'Nutrilite Lean Muscle']),  # Lean Muscle's own label: "CLA helps lose fat, not muscle"
    ('daily-foundations', 'Daily Foundations', 'The everyday base: multivitamins, daily packs, creatine, omega, fiber and gut health.', 'Everything in Daily Foundations', [
        'XS Creatine+', 'Nutrilite Begin Daily GI Primer', 'Nutrilite Balance Within Probiotic',
        'Nutrilite Double X Multivitamin', "Nutrilite Men's Daily Multivitamin Tablets", "Nutrilite Women's Daily Multivitamin Tablets",
        "Nutrilite Organics Men's Daily Multi Gummies", "Nutrilite Organics Women's Daily Multi Gummies",
        "Nutrilite Men's Pack", "Nutrilite Women's Pack", 'Nutrilite Perfect Pack',
        'Nutrilite Concentrated Fruits and Vegetables', 'Nutrilite Cal Mag D', 'Nutrilite Advanced Omega',
        'Nutrilite Prebiotic Fiber', 'Nutrilite Organics Ginger Mint Tea',
        'Nutrilite Vitamin C Extended Release', 'Nutrilite Immunity Defense Zinc + Holy Basil', 'n* by Nutrilite Go Shield']),
    ('skin-redefined', 'Skin Redefined', 'Artistry skincare, for the hours you are not training.', 'Everything in Skin Redefined', [
        'Artistry Skin Nutrition Renewing Softening Toner', 'Artistry Skin Nutrition Sleeping Mask',
        'Artistry Studio Glow Boss Cleanser + Exfoliator', 'Nutrilite Hair, Skin & Nail Health']),
    # DRAFT-COPY (the line after the name): Women's Health, from 2026-09-27. Only what is made for women;
    # the women's pack and multis also stay on Daily Foundations beside the men's, and this is their tag
    # HER PHOTO is the hero: her portrait with their daughter (assets/her/with-daughter-*.webp), shown whole as a
    # real picture beside the name (SHELF_PORTRAIT), since a banner's cover crop cut into their faces. The old
    # placeholder, assets/bg-womens-health.webp (the Women's Pack on a plum field), is kept but no page shows it;
    # drop the SHELF_PORTRAIT entry and it is the banner again. Her story, pairs and DEXA card sit between the
    # hero and the products (SHELF_EXTRA). assets/thumbs|shelf|islands/womens-health.webp are the pack's top,
    # for the 'Keep looking' rows (and the idle strip and ring views)
    ('womens-health', 'Women’s Health', 'For her everyday: the Women’s Pack, multivitamins, iron and menopause support.', 'Everything in Women’s Health', [
        "Nutrilite Women's Pack", "Nutrilite Women's Daily Multivitamin Tablets", "Nutrilite Organics Women's Daily Multi Gummies",
        'Nutrilite Iron Folic', 'Nutrilite Complete Menopause Support']),
    # DRAFT-COPY (the line after the name): Men's Health, its counterpart, the ninth shelf. The men's pack and
    # multis also stay on Daily Foundations, and this is their tag. Concentrated Fruits and Vegetables stays on
    # Daily Foundations only: Amway files it under Men's Health, but nothing on its label is for men.
    # HIS PHOTO is the hero, matching hers: his portrait with their daughter (assets/peter/with-daughter-*.webp),
    # shown whole beside the name (SHELF_PORTRAIT). The old placeholder, assets/bg-mens-health.webp (the Men's
    # Pack on a green field), is kept but no page shows it; drop the SHELF_PORTRAIT entry and it is the banner
    # again. His DEXA card sits between the hero and the products (SHELF_EXTRA).
    ('mens-health', 'Men’s Health', 'For his everyday: the Men’s Pack, multis and Prostate Health.', 'Everything in Men’s Health', [
        "Nutrilite Men's Pack", "Nutrilite Men's Daily Multivitamin Tablets", "Nutrilite Organics Men's Daily Multi Gummies",
        'Nutrilite Prostate Health', 'Nutrilite Organics Horny Goat Weed & Tribulus Capsules']),
    # DRAFT-COPY (the line after the name): Everyday Health, the tenth shelf, 2026-10-01. Peter's call:
    # these four were parked when they were added because none of the nine fitted them, so they get their
    # own shelf rather than being bent onto Daily Foundations. Nothing here is on a second shelf, so this
    # is each one's home shelf and its card tag. Four names that invite claims (cholesterol, liver, heart,
    # aging), so the line, the shelf line and every tagline name the thing and the dose and stop there:
    # the line after the name says how they are taken (what the four labels print, softgels, tablets and
    # capsules once or twice a day), and the part before its colon is the shelf's line in 'Keep looking'.
    # Its hero is assets/bg-everyday-health.webp, a still life in the same house look as the other seven
    # banners: four clear glass columns in an even row on sand against a deep petrol wall, which is also
    # what the shelf means. assets/thumbs|shelf|islands/everyday-health.webp
    # are the same pack's top, for the 'Keep looking' rows (and the idle strip and ring views).
    ('everyday-health', 'Everyday Health', 'The quiet part of the routine: softgels, tablets and capsules, once or twice a day, nothing to mix.', 'Everything in Everyday Health', [
        'Nutrilite Cholesterol Health', 'Nutrilite Liver Support', 'Nutrilite Heart Health CoQ10',
        'Nutrilite Cellular Aging Support']),
]

# The flavor carousel: category slug -> (family prefix to pull, heading, line)
CAROUSELS = {
    'energy-focus': ('XS Energy Drink 12 oz', 'Pick your flavor', 'The 12 oz range, one can at a time.'),
}

# 'bar' is the barbell: the seven shelves as seven weight plates on a rack, each a button that opens a
# panel of that shelf's packs with "Load this plate"; the visitor's loaded plates ride on a bar pinned
# under the masthead, which becomes Peter's bar through #story. 'case' is the stack case: the seven shelves as the seven compartments of one case, each lid a
# button that opens onto a few of that shelf's packs. 'strip' is the tabbed goal strip; 'ring'
# brings back the rotating archipelago. All three are built from the same shelf data, so switching
# is this one word plus a rebuild; the ring's script and styles stay in, idle while it is off.
SHELF_VIEW = 'bar'
CASE_PICKS = 3  # packs an open compartment shows: one per family, in the shelf's own order

# The plates, one per shelf, fixed everywhere the bar theme shows them: colour, and rank on the bar.
# Rank sets size (rank 0 is the full plate, each rank after it 6% smaller) and so place: a bar is
# loaded larger plates nearest the collar. The first five ranks are Peter's stack in the order his
# story loads it, so his bar builds outward and never reshuffles; the five he does not take come last.
# The text on a plate is white or ink, whichever the build finds clears 4.5:1 (it stops if neither does).
# The colours are a satin rubber: Recovery is the XS blue taken down to a bumper plate's (the button's
# --blue read as a toy on a plate), Fat Loss a shade deeper and Hydration a shade lighter, so white and ink
# still clear 4.5:1 under the face's light and shade (measured on the rendered plates, not only here: at
# every face pixel under a letter, since the rack's plates grew to ~160px; both moved a little further for it).
# Women's Health (the eighth, 2026-09-27) is a satin plum, 7.3:1 under white flat and 4.69:1 at its lowest
# rendered pixel anywhere in its words' line boxes on a 390px phone (5.3 at 820 and 1440). Men's Health
# (the ninth, the same day) is a forest green: 7.8:1 flat, 4.81:1 at its lowest on a phone (5.6 wider).
# Everyday Health (the tenth, 2026-10-01) is a satin garnet, a red bumper plate's colour. It was a petrol
# (#2B4E58) at first, which held at plate size but at chip size (the 5x15px key under "Build yours.", and
# the pinned bar) was the same dark mark as Men's green: the two differed almost only along blue-yellow,
# the axis a small patch loses first (CIEDE2000 13.3 apart; 8 once that axis is discounted). Garnet differs
# from Men's on red-green instead (43 apart, 57 discounted); its nearest neighbours now are Fat Loss (16.5)
# and Women's plum (15.0), and it is never within 6 of any plate under a simulated deutan or protan eye
# (the petrol was 2.0 from Women's under protan). White on it is 9.6:1 flat. Rendered (2026-10-01, text
# hidden, the face screenshotted, every pixel in its two lines' text line boxes), white's lowest is 5.89 at
# 390, 7.68 at 820 and 5.78 at 1440 at 1x, and 5.50 / 7.55 / 5.53 at 2x; under the glyphs alone 5.84-7.80.
# The same sweep puts Men's at 4.68 and Women's at 4.51 at their lowest (both at 2x).
PLATES = {
    'recovery': ('#3D4794', 4), 'hydration': ('#93B7C0', 2), 'energy-focus': ('#E2C8AE', 3),
    'protein': ('#1E262F', 0), 'fat-loss': ('#8A543E', 5), 'daily-foundations': ('#6B5646', 1),
    'skin-redefined': ('#D6D4C9', 6), 'womens-health': ('#76485F', 7),
    'mens-health': ('#39594A', 8), 'everyday-health': ('#80222F', 9),
}
# Peter's stack, in the order #story loads it: the shelves his caption strip links to, in the order
# its captions stand, which is also the order the packs land on the shelf (the build checks both).
# The last two go on together, under the one line that folds their two old beats into it. Their places
# ON the bar are PLATES' own ranks, so they fill his five in from his order, not left to right.
PETER = ['protein', 'hydration', 'recovery', 'daily-foundations', 'energy-focus']

# The rack's three-step guide, under "What are we maximizing?" (DRAFT-COPY). The script marks the
# step the visitor is on (aria-current): 1 until a plate is open, 2 while one is, 3 once one is loaded.
# Step 3's two links go where the stack is taken: the call and the sample. Its "Amway" is plain text (an
# <a> with no href: not a link, not in the Tab order) until a plate is on the bar; then the script gives it
# its href and it opens "Take my stack to Amway", as the rack's own .rk-amway buttons do (amwaySync in
# _script.html). With nothing loaded it used to fall through to #my-stack and "Nothing on your bar yet".
# step 3 is Peter's wording (2026-10-01): "add to cart or bring it to a free call or ask for a sample". "Add to
# cart" is the .rg-amway link: plain text until a plate is loaded, then it opens the Amway panel.
RACK_GUIDE = ('<!-- DRAFT-COPY --><ol class="rk-guide" id="rk-guide" role="list" aria-label="How the rack works">'
              '<li class="is-now" aria-current="step"><span class="rg-n" aria-hidden="true">1</span><span class="rg-t">Tap any plate to see the packs on it.</span></li>'
              '<li><span class="rg-n" aria-hidden="true">2</span><span class="rg-t">Load the ones you’d take. They ride up top.</span></li>'
              '<li><span class="rg-n" aria-hidden="true">3</span><span class="rg-t"><a class="rg-amway">Add to cart</a>, bring it to a <a href="#consult">free call</a>, or ask for a <a href="#sample">sample</a>.</span></li>'
              '</ol><!-- /DRAFT-COPY -->')

# "Trending now": the week's three best sellers, between #macros and #story. It is OFF.
# Peter asked for it (2026-10-01: "maybe we should get rid of the trending now, category..."), the
# page ran to thirteen phone screens, and two critics scored the band the weakest thing on the site
# — the counts in bestsellers.csv are blank, so it was three small cards with no numbers on them.
# TO BRING IT BACK: set TRENDING = True here and rebuild. Nothing else. The podium is built on every
# build whether it is shown or not, so bestsellers.csv is still read, the build still fails when a
# name in it is not in share-links.csv, and the three cut-outs are still made. Its markup is the
# `trending` block further down and its CSS is the "Trending: podium" block in style.css, both kept
# whole. The 150-frame pour that could run as the band's ground (TRENDING_POUR) went with it: its
# markup, its ~145 lines of script and its CSS are out, so every page is that much smaller. The
# frames are still in assets/pour/ and the code is one `git show` away.
TRENDING = False

# DRAFT-COPY for Peter's approval: the one line under the name on the case's product card, one per
# family (from the one-liner draft of 2026-09-26). Written to stay clear of Amway's health claims:
# each says what the thing is or when it is used, never what it does for you. Every family needs one.
TAGLINES = {
    'XS Post-Workout Recovery': 'For getting back in the game after training',
    'XS Muscle Multiplier': 'A daily habit alongside your strength training',
    'XS CBD Cream': 'A soothing rub, before or after activity',
    'XS CBD Pro Cream': 'The most CBD of the XS creams',
    'Nutrilite Magnesium': 'Making sure you get enough, every day',
    'Nutrilite Organics Ashwagandha Capsules': 'For the calmer end of a busy day',
    'Nutrilite Organics Chamomile Tea': 'A cup to unwind with in the evening',
    'Nutrilite Sleep Health': 'Part of the wind-down before lights out',
    'n* by Nutrilite Sweet Dreams': 'Blueberry lavender, at the end of the night',
    'XS Sports Twist Tubes': 'Turns your water bottle into a sports drink',
    'Nutrilite Twist Tubes 2GO': 'Three everyday mixes to twist into water',
    'XS CocoWater Hydration Drink Mix': 'Before, during and after the long, hot ones',
    'XS Pre-Workout Boost': 'The last thing before a hard session',
    'XS Energy + Focus Dietary Supplement': 'For giving the workout your full attention',
    'XS Energy Drink 12 oz': 'The no-sugar can for before the session',
    'XS Energy + Burn 12 oz': 'A small coffee’s caffeine, plus green tea extract',
    'XS Juiced and Burn 12 oz': 'Six flavors from two ranges, to find yours',
    'XS Sparkling Juiced Energy 12 oz': 'Made with real fruit juice, no added sugar',
    'XS Elite + Focus Energy Drink': 'The everyday can, with naturally sourced caffeine',
    'XS Grass-Fed Whey Protein': '30 g of protein a scoop, minimal ingredients',
    'XS Grass-Fed Whey Protein Powder Sachets': 'The same 30 g shake, in single servings',
    'XS Sports Protein Bars': 'Between or after workouts, 20 g of protein',
    'XS Sports Protein Shakes': 'Ready to drink, with 25 g of protein',
    'XS Protein Crisps': 'Savory, with 12 g of pea protein a serving',
    'Nutrilite Organics All-in-One Bars': 'For when hunger hits on the go',
    'XS Ignite Powder': 'Caffeine free, neat or mixed into a drink',
    'XS Creatine+': 'A daily 5 g scoop, training day or not',
    'Nutrilite Begin Daily GI Primer': 'A plant-rich drink to start your day',
    'Nutrilite Balance Within Probiotic': 'A daily stick pack, part of the routine',
    'Artistry Skin Nutrition Renewing Softening Toner': 'A milky layer that leaves skin soft',
    'Artistry Skin Nutrition Sleeping Mask': 'Moisture to end the evening routine',
    'Artistry Studio Glow Boss Cleanser + Exfoliator': 'A fresh start for your skin, every day',
    # DRAFT-COPY 2026-09-27, the new families: each is its format and how often, as printed on its label
    'Nutrilite Double X Multivitamin': 'Morning and evening tablets, 22 vitamins and minerals',
    "Nutrilite Men's Daily Multivitamin Tablets": 'One tablet once a day, made for men',
    "Nutrilite Women's Daily Multivitamin Tablets": 'One tablet once a day, made for women',
    "Nutrilite Organics Men's Daily Multi Gummies": 'The daily multi as an organic gummy, for men',
    "Nutrilite Organics Women's Daily Multi Gummies": 'The daily multi as an organic gummy, for women',
    'Nutrilite Iron Folic': 'Iron and folic acid, one to three tablets a day',
    'Nutrilite Complete Menopause Support': 'One tablet a day, made for the menopause years',
    'Nutrilite Prostate Health': 'Saw palmetto and nettle root, a softgel three times a day',
    'Nutrilite Organics Horny Goat Weed & Tribulus Capsules': 'Organic horny goat weed and tribulus, in capsules',
    "Nutrilite Men's Pack": 'One packet a day, put together for men',
    "Nutrilite Women's Pack": 'One packet a day, put together for women',
    'Nutrilite Perfect Pack': 'Two packets a day, with Double X inside',
    'Nutrilite Concentrated Fruits and Vegetables': 'Fruit and vegetable concentrates, one tablet a day',
    'Nutrilite Cal Mag D': 'Calcium, magnesium and D, a tablet three times a day',
    'Nutrilite Advanced Omega': 'Omega softgels, two of them once a day',
    'Nutrilite Prebiotic Fiber': 'One stick pack of fiber, once a day',
    'Nutrilite Organics Ginger Mint Tea': 'Ginger and mint, steeped any time of day',
    'Nutrilite Vitamin C Extended Release': 'One slow-release vitamin C tablet a day',
    'Nutrilite Immunity Defense Zinc + Holy Basil': 'Zinc and holy basil, one tablet twice a day',
    'n* by Nutrilite Go Shield': 'Elderberry lemon gummies with vitamin C and zinc',
    'Nutrilite Joint Health': 'Glucosamine and chondroitin, two tablets twice a day',
    'Nutrilite Organics Turmeric Gummies': 'Organic turmeric gummies in tangerine ginger',
    'Nutrilite Stress Relief Probiotic': 'A once-a-day probiotic capsule',
    'Peak Performance Stack': 'Pre-workout, recovery, Muscle Multiplier and creatine together',
    'Nutrilite Ultra Focus Energy Pack': 'For the long days, one packet once or twice',
    'Nutrilite Memory Builder Supplement': 'Made with cistanche, two tablets once a day',
    "Nutrilite Organics Lion's Mane Mushroom Capsules": 'Organic lion’s mane mushroom, in capsule form',
    'Fitness Jump Start Solution': 'Grass-fed whey plus the XS workout mixes, together',
    'Nutrilite Carb Blocker': 'One to three tablets with your meals',
    'Nutrilite Slimmetry Dietary Supplement': 'One tablet twice a day, alongside your training',
    'Nutrilite Lean Muscle': 'Two CLA softgels, three times a day',
    'Nutrilite Hair, Skin & Nail Health': 'Biotin and collagen, one tablet a day',
    # DRAFT-COPY 2026-10-01, the Everyday Health four: what is in the bottle and how it is taken, off
    # each pack's own label ("60 SOFTGELS | 2 softgels, 1x a day") and nothing else. Their names say more
    # than we can stand behind, so no line here says what any of them is for. CoQ10 is the only ingredient
    # their labels name in legible type, so it is the only one named; amway.com is blocked to us, so none
    # of them carries fact chips either.
    'Nutrilite Cholesterol Health': 'Two softgels once a day, 60 to a bottle',
    'Nutrilite Liver Support': 'One tablet twice a day, 60 to a bottle',
    'Nutrilite Heart Health CoQ10': 'One to three CoQ10 softgels, once a day',
    'Nutrilite Cellular Aging Support': 'Two capsules twice a day, 120 to a bottle',
}

# The quick-fact chips on the case's product card, per listing: (the amway.com page they were read
# off, [2-4 chips]). Composition and format only: grams, milligrams, counts, sizes, "Caffeine free".
# Never a benefit, never a claim. Every chip was read on that page (its Product details and
# Ingredients tabs, through the listing's share link) on 2026-09-27. A listing with no entry shows
# its tagline alone: add one only from its own Amway page, and never guess a number.
AMWAY = 'https://www.amway.com/en_US/'
CARD_FACTS = {
    'XS Post-Workout Recovery - Fruit Punch (12 Stick Packs)': (
        AMWAY + 'XS%E2%84%A2-Post-Workout-Recovery---Fruit-Punch-%2812-Stick-Packs%29-p-316380',
        ['12 stick packs', '5.6 g L-glutamine', '1.5 g glucosamine', '45 calories']),
    'XS Muscle Multiplier - Berry Blast': (
        AMWAY + 'XS%E2%84%A2-Muscle-Multiplier---Berry-Blast-p-126753',
        ['4.1 g essential amino acids', '0 g sugar', '25 calories', '222 g pouch']),
    'Nutrilite Organics Chamomile Tea': (
        AMWAY + 'Nutrilite%E2%84%A2-Organics-Chamomile-Tea-p-308636',
        ['20 tea bags', 'Caffeine free', 'USDA Organic', '0 calories']),
    'XS Sports Twist Tubes - Raspberry Lemonade': (
        AMWAY + 'XS%E2%84%A2-Sports-Twist-Tubes-%E2%80%93-Raspberry-Lemonade-p-305555',
        ['20 tubes', '5 g sugar', '25 calories', '120 mg sodium']),
    'XS Creatine+': (
        AMWAY + 'XS%E2%84%A2-Creatine%2B-p-128463',
        ['5 g creatine monohydrate', '30 servings', 'Unflavored', 'Caffeine free']),
    'Nutrilite Twist Tubes 2GO - Variety Pack': (
        AMWAY + 'Nutrilite%26trade%3B-Twist-Tubes-2GO%26trade%3B-%26ndash%3B-Variety-Pack-p-110922',
        ['20 tubes', '3 flavors', '5–30 calories a tube']),
    'XS Energy Drink 12 oz - Classic': (
        AMWAY + 'XS%E2%84%A2-Energy-Drink-12-oz---Classic-p-126883',
        ['0 g sugar', '114 mg caffeine', '15 calories', '12 cans, 12 fl oz']),
    'XS Pre-Workout Boost - Blue Raspberry (30 Serving Pouch)': (
        AMWAY + 'XS%E2%84%A2-Pre-Workout-Boost---Blue-Raspberry-%2830-Serving-Pouch%29-p-316375',
        ['115 mg caffeine', '4 g beta-alanine', '3.4 g L-citrulline', '30 servings']),
    'XS Energy + Focus Dietary Supplement - 30 Tablets': (
        AMWAY + 'XS%26trade%3B-Energy-%2B-Focus-Dietary-Supplement---30-Tablets-p-107846',
        ['30 tablets', '75 mg caffeine a tablet', 'Caffeine from green tea']),
    'XS Sports Protein Bars - Chocolate Peanut Butter': (
        AMWAY + 'XS%E2%84%A2-Sports-Protein-Bars-%E2%80%93-Chocolate-Peanut-Butter-p-110385',
        ['20 g protein', '12 bars', 'Gluten free']),
    'XS Grass-Fed Whey Protein - Chocolate': (
        AMWAY + 'XS%E2%84%A2-Grass-Fed-Whey-Protein-%E2%80%93-Chocolate-p-128154',
        ['30 g protein', '20 servings', 'Grass-fed whey', '1 g sugar']),
    'XS Sports Protein Shakes - Rich Chocolate': (
        AMWAY + 'XS%E2%84%A2-Sports-Protein-Shakes-%E2%80%93-Rich-Chocolate-p-110369',
        ['25 g protein', '1 g sugar', '12 shakes', 'Ready to drink']),
    'XS Ignite Powder - Moro Blood Orange': (
        AMWAY + 'XS%E2%84%A2-Ignite-Powder-%E2%80%93-Moro-Blood-Orange-p-127811',
        ['30 sachets', 'Caffeine free', '15 calories', 'Gluten free']),
    'Nutrilite Begin Daily GI Primer': (
        AMWAY + 'Nutrilite-Begin%E2%84%A2-Daily-GI-Primer-p-127725',
        ['30 servings', '4 g fiber', '30 calories', '<1 g sugar']),
    'Nutrilite Balance Within Probiotic': (
        AMWAY + 'Nutrilite%E2%84%A2-Balance-Within%E2%84%A2-Probiotic-p-120571',
        ['30 stick packs', '6.3 billion CFU', '5 probiotic strains']),
    'Artistry Skin Nutrition Sleeping Mask': (
        AMWAY + 'Artistry-Skin-Nutrition%E2%84%A2-Sleeping-Mask-p-125575',
        ['80 mL', 'Leave-on mask', 'With niacinamide']),
    'Artistry Skin Nutrition Renewing Softening Toner': (
        AMWAY + 'Artistry-Skin-Nutrition%E2%84%A2-Renewing-Softening-Toner--p-123783V',
        ['200 mL', 'pH balanced', 'No animal-derived ingredients']),
    'Artistry Studio Glow Boss Cleanser + Exfoliator': (
        AMWAY + 'Artistry-Studio%E2%84%A2-Glow-Boss-Cleanser-%2B-Exfoliator-p-124812',
        ['125 mL', 'Vegan', 'pH balanced', 'No parabens']),
}

# The product card's sound, by family: 'can' (a can cracking open and fizzing), 'level' (a short
# rising arpeggio) or, for anything not named here, 'chime'. _script.html synthesises all three
# inside the interface sound, so the mute button covers them and there is nothing to download.
CARD_SOUND = {
    'XS Creatine+': 'level', 'Peak Performance Stack': 'level', 'Fitness Jump Start Solution': 'level',
    'XS Energy Drink 12 oz': 'can', 'XS Energy + Burn 12 oz': 'can', 'XS Juiced and Burn 12 oz': 'can',
    'XS Sparkling Juiced Energy 12 oz': 'can', 'XS Elite + Focus Energy Drink': 'can',
    # the Everyday Health four take the default chime; named here so the shelf is wired end to end
    'Nutrilite Cholesterol Health': 'chime', 'Nutrilite Liver Support': 'chime',
    'Nutrilite Heart Health CoQ10': 'chime', 'Nutrilite Cellular Aging Support': 'chime',
}

SHELF_LINE = {  # the line under each shelf name
    'recovery': 'After the session', 'hydration': 'Long, hot sessions', 'energy-focus': 'Before the session',
    'protein': 'Hitting your protein', 'fat-loss': 'Training to lean out', 'daily-foundations': 'Everyday basics',
    'skin-redefined': 'Skin & overnight', 'womens-health': 'For her everyday',
    'mens-health': 'For his everyday',
    'everyday-health': 'Day in, day out',  # DRAFT-COPY, all three: a habit, like the others, not a count
}

CAT_THUMB = {  # the pack shown on the homepage row for each category
    'recovery': 'XS Post-Workout Recovery - Fruit Punch (12 Stick Packs)',
    'hydration': 'XS Sports Twist Tubes - Raspberry Lemonade',
    'energy-focus': 'XS Energy Drink 12 oz - Classic',
    'protein': 'XS Sports Protein Bars - Chocolate Peanut Butter',
    'fat-loss': 'XS Ignite Powder - Moro Blood Orange',
    'daily-foundations': 'XS Creatine+',
    'skin-redefined': 'Artistry Skin Nutrition Sleeping Mask',
    'womens-health': "Nutrilite Women's Pack", 'mens-health': "Nutrilite Men's Pack",
    'everyday-health': 'Nutrilite Cellular Aging Support',
}

# Calendly link for the consult section; it embeds inline on submit rather than opening a tab.
# The four answers ride along as a1-a4, onto the event type's four custom questions in order;
# leave it empty and the form says the calendar is not connected yet instead of embedding nothing.
CONSULT_URL = 'https://calendly.com/3pete/explore'

# The quick 10-minute call: the invitation under the free-sample form and in its thank-you, and
# step 4 of "The game plan" (#how). Paste the 10-minute Calendly event's link here and rebuild;
# its label and link switch on at build time (see quick_call below), and _script.html opens it in
# Calendly's popup. While it is empty nothing claims a 10-minute call: the button says "Book a
# free call" and goes to #consult, the 30-minute booking already on the page.
CONSULT_QUICK_URL = ''

# The free-sample form (#sample on the homepage) posts to FormSubmit, which needs no account: the
# first real request sends an activation email to this inbox, and once it is confirmed FormSubmit
# offers a random alias to use instead. Swap the address for that alias here; nothing else names it.
# With script the form posts JSON to the ajax endpoint; without, it is a plain POST to the action,
# and FormSubmit sends the visitor back to SAMPLE_NEXT, where :target shows the thank-you.
SAMPLE_TO = 'peterherschelman@gmail.com'

# Where the site actually lives. Everything else on the site is linked relatively; this is
# only for the absolute URLs that Open Graph and Twitter cards require. GitHub Pages serves
# the repo from a subpath, so the trailing slash matters. Move to a custom domain and this
# one line is the whole change — nothing else hardcodes the host.
BASE = 'https://3p3t3.github.io/RAW/'

SAMPLE_ENDPOINT = 'https://formsubmit.co/ajax/' + SAMPLE_TO
SAMPLE_ACTION = 'https://formsubmit.co/' + SAMPLE_TO
SAMPLE_NEXT = BASE + 'homepage.html?sample=sent#sample-sent'

FEATURED = [  # props-free pack shots, so the grid reads as one series
    'XS Grass-Fed Whey Protein - Chocolate',
    'XS Post-Workout Recovery - Fruit Punch (30 Serving Pouch)',
    'XS Pre-Workout Boost - Blue Raspberry (30 Serving Pouch)',
    'XS Creatine+',
    'XS Energy Drink 12 oz - Classic',
    'XS Muscle Multiplier - Berry Blast',
    'XS Sports Protein Shakes - Rich Chocolate',
    'Nutrilite Organics Chamomile Tea',
]

GOAL_NAMES = {'R': 'Recovery', 'L': 'Lean mass', 'E': 'Endurance', 'S': 'Sleep'}

GOAL_TILES = [  # goal, name, line, product shown in the goal index
    ('R', 'Recovery', 'Bounce back between sessions', 'XS Post-Workout Recovery - Fruit Punch (12 Stick Packs)'),
    ('L', 'Lean Mass', 'Build muscle and keep it', 'XS Sports Protein Bars - Chocolate Peanut Butter'),
    ('E', 'Endurance', 'Energy and hydration that lasts', 'XS Sports Twist Tubes - Raspberry Lemonade'),
    ('S', 'Sleep &amp; Longevity', 'Rest deeper, age well', 'Nutrilite Sleep Health'),
]

# ---- His and hers: the proof after #story, Yenni's story on Women's Health, and the DEXA cards ----
# Peter's wife runs the women's side of the business; Peter approved her name, photos and results going
# public. HER_NAME is her first name as the site shows it ("Yenni", as Peter introduced her; never the
# longer name on her scan reports). Empty, nothing shows a gap: every line that names her has a second
# wording without the name (see her_says), in Peter's voice ("my wife") or with "she".
HER_NAME = 'Yenni'
HER_SURNAME = 'Herschelman'  # only where a full name reads naturally: the intro on her shelf


def her_says(named, unnamed):
    """One line of copy about her: `named` with {n} (first name) and {full} filled in, or `unnamed` while
    HER_NAME is empty."""
    return named.format(n=HER_NAME, full=f'{HER_NAME} {HER_SURNAME}') if HER_NAME else unnamed


# DEXA scans, both at the same clinic. The cards are drawn from these rows and nothing else: never the report,
# its layout, its logo or colours, and nothing else from it (no birth date, patient ID or height).
# A row is (date, weight lb, fat lb, lean lb, body fat %). Its date is 'YYYY-MM-DD', or 'YYYY-MM' when only the
# month is known; the cards show month and year either way. Weight is kept for the record and never shown.
# A card's headline is its first scan against its last. The scans are their own timeline: they are never
# presented as covering the same months as the before/after photos.
DEXA_AT = 'UC Davis Sports Medicine, Sacramento'   # Peter is from Lincoln, nearby: the name says "local"
# DRAFT-COPY: under every DEXA card, in this order
DEXA_NOTES = [f'Measured by DEXA scan at {DEXA_AT}.',
              'We’re not sponsored by or affiliated with UC Davis Health; we’re just big fans of their DEXA service.',
              'Individual results vary.']
# Hers. Set HER_DEXA = None and her card comes off every page. 'gap' is the index of the scan after which there
# is none until the next: the trend is drawn broken there (no line across it), and the card says why.
# Peter's card: his transformation, by DEXA scan at the start and end of the fifteen months his before/after
# photos span, as (weight lb, body fat %, fat lb, lean lb) before and after. EVERY figure is read off his
# reports — he relayed them rather than uploading (2026-09-28) — so nothing here is derived and the card
# carries no worked-it-out line. The rows do not sum to the weight, and should not be made to: a DEXA total
# also carries bone mineral. He chose no dates and no clinic (his later scans at UC Davis are not used).
PETER_TRANSFORM = ((170, 22.1, 38.1, 132.7), (164, 7.4, 12.3, 152.1))
# The fat and lean rows. Set PETER_SHOW_COMPOSITION = False and both come off the card in one edit.
PETER_SHOW_COMPOSITION = True
HER_DEXA = {
    'scans': [('2024-01', 137.8, 41.2, 92.1, 29.9), ('2024-07', 142.0, 41.8, 95.7, 29.4),
              ('2024-12', 134.5, 39.0, 90.9, 29.0), ('2026-08-21', 132.9, 30.2, 98.1, 22.7)],
    # no scan from Dec 2024 to Aug 2026: she was pregnant from Dec 2024, and their daughter was born in Sep 2025
    'gap': 2,
    'gap_why': 'we got pregnant and had our first in between',   # DRAFT-COPY (Peter's words)
}
# The before/after photos in assets/her/ (placed by hand; CLAUDE.md): their own dates, not the scans'
HER_PHOTOS = ('Nov 2025', 'Jul 2026')
# Peter's before/after are labelled by month of his fifteen, not by calendar date: his choice (2026-10-01).
# The proof wall shows them where Yenni's dates go, and the story's Before/After tags carry them too.
PETER_PHOTOS = ('Month 1', 'Month 15')

MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()


def when(d):
    """'YYYY-MM[-DD]' -> (the date as a fractional year, for the x axis; 'Mon YYYY', for the words)."""
    y, m, *day = (int(x) for x in d.split('-'))
    return y + (m - 1 + ((day[0] if day else 15) - 1) / 31) / 12, f'{MONTHS[m - 1]} {y}'


def dexa_chart(d, k, colour, title):
    """One small trend: a single measure (column k of the scans) on a time-true x axis from the first scan to
    the last, and a y axis from zero, so a change is drawn at its real size. Where the scans have a gap the
    line stops, and the gap is a shaded band marked "no scans": nothing is drawn where nothing was measured.
    Only the first and last values are labelled; each point names its month and value on hover."""
    W, H, L, R, T, B = 300, 132, 36, 16, 20, 26
    s, gap = d['scans'], d.get('gap')
    t = [when(r[0])[0] for r in s]
    v = [r[k] for r in s]
    top = -(-max(v) * 1.08 // 10) * 10                      # zero to the next ten above the highest value
    X = lambda x: L + (x - t[0]) / (t[-1] - t[0]) * (W - L - R)
    Y = lambda y: T + (1 - y / top) * (H - T - B)
    o = []
    for g in (0, top / 2, top):
        o.append(f'<line class="dx-grid{" dx-base" if not g else ""}" x1="{L}" x2="{W - R + 4}" y1="{Y(g):.1f}" y2="{Y(g):.1f}"/>'
                 f'<text class="dx-yl" x="{L - 7}" y="{Y(g) + 4:.1f}" text-anchor="end">{g:g}</text>')
    y0 = int(t[0])
    for x, y, a in [(t[0], y0, 'start')] + [(float(y), y, 'middle') for y in range(y0 + 1, int(t[-1]) + 1)]:
        o.append(f'<line class="dx-tick" x1="{X(x):.1f}" x2="{X(x):.1f}" y1="{H - B}" y2="{H - B + 4}"/>'
                 f'<text class="dx-xl" x="{X(x) - (4 if a == "start" else 0):.1f}" y="{H - 7}" text-anchor="{a}">{y}</text>')
    if gap is not None:
        a, b = X(t[gap]) + 8, X(t[gap + 1]) - 8
        o.append(f'<rect class="dx-gap" x="{a:.1f}" y="{T - 6}" width="{b - a:.1f}" height="{H - B - T + 6}"/>'
                 f'<text class="dx-gapl" x="{(a + b) / 2:.1f}" y="{T + (H - T - B) / 2 + 4:.1f}" text-anchor="middle">no scans</text>')
    runs = [list(range(len(v)))] if gap is None else [list(range(gap + 1)), list(range(gap + 1, len(v)))]
    for r in runs:
        if len(r) > 1:
            o.append(f'<polyline class="dx-line" points="{" ".join(f"{X(t[i]):.1f},{Y(v[i]):.1f}" for i in r)}" stroke="{colour}"/>')
    for i in range(len(v)):
        o.append(f'<circle class="dx-pt" cx="{X(t[i]):.1f}" cy="{Y(v[i]):.1f}" r="4" fill="{colour}">'
                 f'<title>{when(s[i][0])[1]}: {v[i]:.1f} lb</title></circle>')
    for i, a in ((0, 'start'), (len(v) - 1, 'end')):
        o.append(f'<text class="dx-vl" x="{X(t[i]) + (2 if a == "start" else 6):.1f}" y="{Y(v[i]) - 9:.1f}" text-anchor="{a}">{v[i]:.1f}</text>')
    return (f'<figure class="dx-chart"><figcaption class="dx-ct"><i style="--c:{colour}"></i>{title}</figcaption>'
            f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true" focusable="false">{"".join(o)}</svg></figure>')


def dexa_card(d, title, level=3, span_line=None):
    """The DEXA card: who, how many scans over when, the first scan against the last (body fat, fat, lean
    mass), the fat and lean trends, and the source and disclaimer. One component for both of them."""
    s, gap = d['scans'], d.get('gap')
    a, b = s[0], s[-1]
    first, last = when(a[0])[1], when(b[0])[1]

    def delta(x, unit, held=0.0):
        return 'held' if abs(x) < held else f'{"+" if x > 0 else "−"}{abs(x):.1f} {unit}'
    nums = [('Body fat', f'{a[4]:.1f}% → {b[4]:.1f}%', delta(b[4] - a[4], 'points')),
            ('Fat', f'{a[2]:.1f} → {b[2]:.1f} lb', delta(b[2] - a[2], 'lb')),
            ('Lean mass', f'{a[3]:.1f} → {b[3]:.1f} lb', delta(b[3] - a[3], 'lb', held=1.0))]
    words = {4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight'}
    span = span_line or f'{words.get(len(s), len(s))} scans, {first} → {last}'
    gap_line = (f'<p class="dx-gapnote">No scan between {when(s[gap][0])[1]} and {when(s[gap + 1][0])[1]}: '
                f'{d["gap_why"]}.</p>') if gap is not None else ''
    rows = ''.join(f'<tr><th scope="row">{when(r[0])[1]}</th><td>{r[4]:.1f}%</td><td>{r[2]:.1f} lb</td><td>{r[3]:.1f} lb</td></tr>' for r in s)
    return (f'<!-- DRAFT-COPY --><article class="dx-card" aria-labelledby="dx-{slug(title)}">\n'
            f'<div class="dx-head"><h{level} class="dx-t" id="dx-{slug(title)}">{title}</h{level}><p class="dx-span">{span}</p></div>\n'
            '<dl class="dx-nums">' + ''.join(f'<div class="dx-n"><dt>{k}</dt><dd class="dx-v">{v}</dd><dd class="dx-d">{dd}</dd></div>' for k, v, dd in nums) + '</dl>\n'
            f'{gap_line}'
            '<div class="dx-charts">' + dexa_chart(d, 2, '#8A543E', 'Fat mass, lb') + dexa_chart(d, 3, '#3340B8', 'Lean mass, lb') + '</div>\n'
            f'<div class="vh"><table><caption>{title}, every scan</caption><thead><tr><th scope="col">Scan</th><th scope="col">Body fat</th>'
            f'<th scope="col">Fat mass</th><th scope="col">Lean mass</th></tr></thead><tbody>{rows}</tbody></table></div>\n'
            '<div class="dx-src">' + ''.join(f'<p>{n}</p>' for n in DEXA_NOTES) + '</div>\n'
            '</article><!-- /DRAFT-COPY -->')


def peter_card(level=3):
    """Peter's DEXA card: the two scans of his transformation, fifteen months apart, as body fat and weight
    (PETER_TRANSFORM), then — while PETER_SHOW_COMPOSITION is on — its pounds of fat and lean. Every
    figure is off the report. No dates, no trend, no clinic: that is all he chose to show."""
    (w0, f0, fat0, lean0), (w1, f1, fat1, lean1) = PETER_TRANSFORM
    nums = [('Body fat', f'{f0:.1f}% → {f1:.1f}%', f'−{f0 - f1:.1f} points'),
            ('Weight', f'{w0} → {w1} lb', f'−{w0 - w1} lb')]
    if PETER_SHOW_COMPOSITION:
        nums += [('Fat', f'{fat0:.1f} → {fat1:.1f} lb', f'−{fat0 - fat1:.1f} lb'),
                 ('Lean mass', f'{lean0:.1f} → {lean1:.1f} lb', f'+{lean1 - lean0:.1f} lb')]
    t = 'Peter’s DEXA scans'
    return (f'<!-- DRAFT-COPY --><article class="dx-card" aria-labelledby="dx-{slug(t)}">\n'
            f'<div class="dx-head"><h{level} class="dx-t" id="dx-{slug(t)}">{t}</h{level}><p class="dx-span">Two scans, fifteen months apart</p></div>\n'
            f'<dl class="dx-nums{" dx-four" if PETER_SHOW_COMPOSITION else ""}">'
            + ''.join(f'<div class="dx-n"><dt>{k}</dt><dd class="dx-v">{v}</dd><dd class="dx-d">{dd}</dd></div>' for k, v, dd in nums) + '</dl>\n'
            f'<div class="dx-src"><p>Measured by DEXA scan.</p><p>Individual results vary.</p></div>\n'
            '</article><!-- /DRAFT-COPY -->')


def dexa_cards(level=3, who=('peter', 'her')):
    """Peter's card, then hers once HER_DEXA is filled."""
    out = []
    if 'peter' in who:
        out.append(peter_card(level))
    if 'her' in who and HER_DEXA:
        out.append(dexa_card(HER_DEXA, her_says('{n}’s DEXA scans', 'Her DEXA scans'), level))
    return '\n'.join(out)


def her_pairs(caption, cls='', unnamed='My wife'):
    """Her two before/after pairs, front and back, framed to one spec like Peter's three, so one row of
    Before / After headings on the 50% line labels both. Their dates are the photos' own."""
    who, alt = her_says('{n}', unnamed), her_says('{n}', 'Peter’s wife')
    imgs = ''.join(
        f'<img src="assets/her/{v}-640.webp" srcset="assets/her/{v}-640.webp 640w, assets/her/{v}-768.webp 768w" '
        f'sizes="(min-width:1000px) 460px, (min-width:760px) 560px, calc(100vw - 40px)" width="768" height="979" '
        f'loading="lazy" decoding="async" alt="{esc(alt)}, before and after, from the {v}: {HER_PHOTOS[0]} and {HER_PHOTOS[1]}">'
        for v in ('front', 'back'))
    return (f'<figure class="c-proof pf-hers{cls}">\n'
            f'  <!-- DRAFT-COPY --><p class="pf-who"><span class="pf-name">{who}</span> <span class="pf-when">{HER_PHOTOS[0]} → {HER_PHOTOS[1]}</span></p><!-- /DRAFT-COPY -->\n'
            '  <div class="c-cols" aria-hidden="true"><span>Before</span><span>After</span></div>\n'
            f'  <div class="c-stack">{imgs}</div>\n'
            f'  <!-- DRAFT-COPY --><figcaption>{caption}</figcaption><!-- /DRAFT-COPY -->\n'
            '</figure>')


def her_text(label='Who runs this shelf', level=2, tid='her-title', title=None):
    """Yenni in words, in the first person (Peter asked for it on 2026-10-01; it stays DRAFT until she has read
    it): who she is, when her photos were taken, and what changed. Shared by the Women's
    Health shelf (through her_story) and by about.html, which puts her under its own "Who we are"
    heading: no eyebrow (label=None), her name as the heading (title) one level down, and its id."""
    label_p = f'<p class="label">{label}</p>\n        ' if label else ''
    return f'''<!-- DRAFT-COPY --><div class="her-text grow">
        {label_p}<h{level} id="{tid}">{title or her_says('{n}’s story', 'Her story')}</h{level}>
        <p class="her-lead">{her_says('I’m {n} — Peter’s wife, and I run the women’s side of Aspire Health.', 'I’m Peter’s wife, and I run the women’s side of Aspire Health.')}</p>
        <p>Our daughter was born in September 2025. I started lifting with progressive overload while I was pregnant.</p>
        <p>My before photos are from November 2025, two months postpartum, so they include the body fat a pregnancy adds. My afters are from July 2026.</p>
        <h{level + 1} class="her-h">What changed</h{level + 1}>
        <ul class="c-list">
          <li>Progressive overload: lifting a little more over time</li>
          <li>Counting calories</li>
          <li>Solid supplementation</li>
          <li>Creatine, for the first time</li>
        </ul>
        <p class="her-fine">Individual results vary.</p>
      </div><!-- /DRAFT-COPY -->'''


def peter_text(level=3, tid='his-title'):
    """Peter in words, in his own voice: the bio line he wrote for the call, what Aspire Health is, and
    what changed over his fifteen months. The bullets are built from his own lines in the story (his
    food, someone who pushed him, his sleep through the newborn nights, the supplement testing) without
    repeating any of them word for word. about.html only, under its "Who we are" heading, beside hers."""
    return f'''<div class="her-text grow">
        <h{level} id="{tid}">Peter</h{level}>
        <!-- PETER-COPY --><p class="her-lead">I’m Peter — husband, dad to a baby girl, and a Lincoln local. My wife’s as obsessed with biohacking and longevity as I am.</p><!-- /PETER-COPY -->
        <!-- DRAFT-COPY --><p>Aspire Health is the two of us, out of Lincoln, California. {her_says('{n}', 'My wife')} runs the women’s side; the rest is mine.</p><!-- /DRAFT-COPY -->
        <h{level + 1} class="her-h">What changed</h{level + 1}>
        <!-- PETER-COPY: approved 2026-10-01 --><ul class="c-list">
          <li>Lifting hard, with someone who pushed me</li>
          <li>Fixing my food, which meant counting calories</li>
          <li>Trying supplements myself until I knew what was worth taking</li>
          <li>Making the most of my sleep, newborn nights included</li>
        </ul><!-- /PETER-COPY -->
        <p class="her-fine">Individual results vary.</p>
      </div>'''


def her_story():
    """Women's Health only: Yenni's story, her pairs and her DEXA card, between the hero and the shelf."""
    return f'''  <!-- Her story: only the Women's Health shelf has this block (SHELF_EXTRA in build_homepage.py). Facts only;
       no health claims, and nothing says a supplement caused the change: it was her whole plan. -->
  <section class="sec her-sec" id="her" aria-labelledby="her-title">
    <div class="wrap her-in">
      {her_text()}
      {her_pairs('Before: two months postpartum. After: ten months postpartum.', ' grow', 'Her photos')}
      {dexa_cards(3, ('her',))}
    </div>
  </section>

'''


def peter_numbers():
    """Men's Health only: Peter's DEXA card, above the shelf."""
    return ('  <!-- Peter\'s DEXA card: only the Men\'s Health shelf has this block (SHELF_EXTRA in build_homepage.py) -->\n'
            '  <section class="sec dx-sec" aria-label="Peter’s DEXA scans">\n    <div class="wrap dx-one">\n'
            + dexa_cards(2, ('peter',)) + '\n    </div>\n  </section>\n\n')


# A shelf page's own block, between its hero and its products; only these two have one
SHELF_EXTRA = {'womens-health': her_story, 'mens-health': peter_numbers}
# A shelf whose hero is a real photo rather than a banner: it is shown whole, beside the name on wide
# screens and above it on phones, because a banner's cover crop would cut into their faces
SHELF_PORTRAIT = {
    'womens-health': ('assets/her/with-daughter', 640, 960, 5 / 4,
                      her_says('{n} holding their baby daughter, both in matching lemon-print dresses',
                               'Peter’s wife holding their baby daughter, both in matching lemon-print dresses')),
    'mens-health': ('assets/peter/with-daughter', 640, 960, 5 / 4, 'Peter holding their baby daughter'),
}


def hero_media(slug_, name):
    """The shelf hero's picture: its banner (assets/bg-<slug>.webp) under the name, or a portrait beside it."""
    if slug_ not in SHELF_PORTRAIT:
        return {'{{CAT_HERO_CLASS}}': '', '{{CAT_HERO_MEDIA}}': (
            f'<img class="cat-bg" src="assets/bg-{slug_}.webp" alt="" width="1600" height="900" fetchpriority="high">')}
    base, w1, w2, ratio, alt = SHELF_PORTRAIT[slug_]
    return {'{{CAT_HERO_CLASS}}': ' cat-hero-photo', '{{CAT_HERO_MEDIA}}': (
        f'<div class="wrap cat-pic"><figure class="cat-portrait"><img src="{base}-{w1}.webp" '
        f'srcset="{base}-{w1}.webp {w1}w, {base}-{w2}.webp {w2}w" sizes="(min-width:760px) min(38vw, 440px), calc(100vw - 40px)" '
        f'width="{w2}" height="{round(w2 * ratio)}" alt="{esc(alt)}" fetchpriority="high"></figure></div>')}




def about_portraits():
    """about.html's hero: their two portraits with their daughter, his then hers, taken from the same
    SHELF_PORTRAIT rows the two his-and-hers shelves are headed with, so the files and the alt text
    have one home. Shown whole, side by side, never cover-cropped."""
    return '\n'.join(
        f'      <figure class="cat-portrait"><img src="{b}-{w1}.webp" srcset="{b}-{w1}.webp {w1}w, {b}-{w2}.webp {w2}w" '
        f'sizes="(min-width:760px) min(26vw, 300px), calc(50vw - 30px)" width="{w2}" height="{round(w2 * r)}" '
        f'alt="{esc(a)}" fetchpriority="high"></figure>'
        for b, w1, w2, r, a in (SHELF_PORTRAIT['mens-health'], SHELF_PORTRAIT['womens-health']))


def his_pairs(caption='Fifteen-month transformation.'):
    """Peter's three before/after views, front, side and back. Each file is one photo cut to one shared
    framing spec with the seam at exactly 50%, so the befores line up down the left and the afters down
    the right, and one pair of headings on that 50% line labels all three (CLAUDE.md: his body is never
    retouched). Moved out of homepage.template.html when the proof became about.html."""
    imgs = ''.join(
        f'<img src="assets/peter/{v}-640.webp" srcset="assets/peter/{v}-640.webp 640w, assets/peter/{v}-960.webp 960w" '
        f'sizes="(min-width:760px) 680px, calc(100vw - 40px)" width="960" height="640" loading="lazy" '
        f'decoding="async" alt="Peter, before and after, from the {v}">' for v in ('front', 'side', 'back'))
    return (f'<figure class="c-proof pf-his">\n'
            # PETER-COPY: his photos are labelled by month, not date (Peter, 2026-10-01: "month one, month 15")
            f'  <p class="pf-who"><span class="pf-name">Peter</span> <span class="pf-when">{PETER_PHOTOS[0]} → {PETER_PHOTOS[1]}</span></p>\n'
            '  <div class="c-cols" aria-hidden="true"><span>Before</span><span>After</span></div>\n'
            f'  <div class="c-stack">{imgs}</div>\n'
            f'  <!-- PETER-COPY --><figcaption>{caption}</figcaption><!-- /PETER-COPY -->\n'
            '</figure>')


def proof_wall():
    """The proof wall, his and hers: Peter's three views, and beside them (under them on a phone) his
    wife's two, nothing to swipe. about.html's "what changed"; it used to close the homepage's story."""
    return ('    <!-- DRAFT-COPY --><h2 class="pf-title" id="proof-t"><span class="pf-k">His</span> and <span class="pf-k">hers</span></h2><!-- /DRAFT-COPY -->\n'
            '    <div class="pf-duo">\n      ' + his_pairs() + '\n      '
            + her_pairs('Before: two months postpartum.') + '\n    </div>')


# about.html's own two lines: its meta description (and og:description) and the line under its title.
# DRAFT-COPY, both of them.
ABOUT_TAG = her_says(
    'Peter and {full}, the two people behind Aspire Health: who we are, our before and afters, and our DEXA scans.',
    'The two people behind Aspire Health: who we are, our before and afters, and our DEXA scans.')
ABOUT_SUB = her_says('Peter and {n} Herschelman. Who we are, what changed, and the scans behind it.',
                     'Peter and his wife. Who we are, what changed, and the scans behind it.')


def normalize(src, dst, size=600):
    """Trim each cut-out to the product, fit it to one box and stand it on a shared baseline,
    so every photo in the grid reads at the same scale. Falls back to a plain copy without Pillow."""
    # the cache keys on the source photo's mtime and on the text of this function: edit the trimming or
    # scaling below and the fingerprint stops matching assets/.cut-version, which re-cuts everything.
    if not RECUT and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return
    try:
        from PIL import Image
    except ImportError:
        shutil.copyfile(src, dst)
        return
    im = Image.open(src).convert('RGBA')
    box = im.getchannel('A').point(lambda a: 255 if a > 60 else 0).getbbox() or (0, 0, *im.size)
    im = im.crop(box)
    px = im.load()
    w, h = im.size
    for y in range(int(h * .8), h):  # pale, semi-transparent floor reflections read as smudges on tinted tiles
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 235 and min(r, g, b) > 170:
                px[x, y] = (r, g, b, 0)  # pale reflection
            elif a < 150:
                px[x, y] = (r, g, b, 0)  # soft baked-in shadow; the page draws one consistent shadow instead
    box = im.getchannel('A').point(lambda a: 255 if a > 60 else 0).getbbox() or (0, 0, w, h)
    im = im.crop(box)
    w, h = im.size
    k = min(size * .56 / (w * h) ** .5, size * .9 / w, size * .8 / h)  # equal visual mass, capped to the box
    im = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.paste(im, ((size - im.width) // 2, round(size * .91) - im.height), im)
    out.save(dst, quality=86, method=6)


def cut_version():
    return hashlib.sha1(inspect.getsource(normalize).encode()).hexdigest()[:12]


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def family(name):
    best = max((k for k in FAMILIES if name == k or name.startswith(k + ' ')), key=len, default=None)
    if not best:
        raise SystemExit(f'No family rule for product: {name!r} (add it to FAMILIES)')
    return best


def describe(p):
    fam = family(p['product'])
    kind, goals, form = FAMILIES[fam]
    base, _, variant = p['product'].partition(' - ')
    display = base.replace(' 12 oz', '').replace('n- by Nutrilite', 'n* by Nutrilite')
    variant = re.sub(r'\s*\((\d+) Serving Pouch\)', r', \1-serving pouch', variant)
    variant = re.sub(r'\s*\((\d+) Stick Packs\)', r', \1 stick packs', variant)
    variant = re.sub(r'^(\d+) Tablets$', r'\1 tablets', variant)
    desc = kind + (' · ' + variant if variant else '')
    return dict(p, name=display, desc=desc, goals=goals, form=form)


def plural(n, noun, zero=None):
    """`1 product`, `2 products`, and something that reads at 0.

    Every count on the site goes through here, so the noun is never written out beside a
    number by hand and the next single-product shelf pluralizes itself.
    """
    if n == 0:
        return zero if zero is not None else f'no {noun}s'
    return f'{n} {noun}' if n == 1 else f'{n} {noun}s'


def _lum(h):
    c = [int(h.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


def plate_ink(colour):
    """White or ink on a plate: whichever clears 4.5:1, white first (it is the one the dark plates want)."""
    for ink in ('#FFFFFF', '#1E262F'):
        if contrast(colour, ink) >= 4.5:
            return ink
    raise SystemExit(f'PLATES: nothing reads on {colour} at 4.5:1')


def barbell(cls, loaded=None):
    """A barbell, side on: two sleeves of plates either side of the collars, and the shaft with its
    knurled centre between them. With `loaded` (shelf slugs) it is drawn loaded and never changes;
    without, every plate is on both sleeves, unloaded, for the script to load (_script.html). Plates
    sit at the collar and step outward by rank; style.css draws everything from the bar's font-size."""
    slugs = sorted(loaded if loaded is not None else PLATES, key=lambda k: PLATES[k][1])
    def plates():
        out = []
        for k in slugs:
            col, rank = PLATES[k]
            o = sum(1 for j in slugs if PLATES[j][1] < rank) if loaded is not None else 0
            out.append(f'<i class="bb-p{" on" if loaded is not None else ""}" data-cat="{k}" '
                       f'style="--c:{col};--s:{1 - .06 * rank:.2f};--o:{o}"><b class="bb-ring"></b></i>')
        return ''.join(out)
    # the sleeves hold every plate there is (--n, style.css). Peter's bars drawn loaded (the story's arc and
    # "That's my stack") only ever carry his five, so they keep the seven-plate sleeve they were drawn with
    # (a nine-plate one would push "That's my stack" past its box on a phone)
    n = len(PLATES) if loaded is None else 7
    return (f'<div class="bb {cls}" style="--n:{n}" aria-hidden="true"><span class="bb-sl bb-l">{plates()}</span><span class="bb-co"></span>'
            f'<span class="bb-sh"><span class="bb-kn"></span></span><span class="bb-co"></span>'
            f'<span class="bb-sl bb-r">{plates()}</span></div>')


def esc(s):
    return html.escape(s, quote=True)


def shot(p, lazy=True, cls='shot'):
    if p.get('studio'):
        cls += ' shot-studio'
    if p['img']:
        ld = 'loading="lazy" ' if lazy else ''
        return f'<span class="{cls}"><img src="{p["img"]}" alt="" {ld}width="600" height="600"></span>'
    return f'<span class="ph" aria-hidden="true"><span class="ph-cap"><b>Photo</b><br>coming soon</span></span>'


def quick_call():
    """The quick call's words and button, switched on CONSULT_QUICK_URL. All of it is DRAFT-COPY."""
    if CONSULT_QUICK_URL:
        return {
            '{{QUICK_ASK}}': 'Want a quick 10 min to figure out how to optimize this in your routine? Book a consult here.',
            '{{QUICK_STEP}}': 'Ten minutes on the phone to find where it slots in',
            '{{QUICK_CALL}}': f'<a class="btn q-go" href="{esc(CONSULT_QUICK_URL)}" target="_blank" rel="noopener" '
                              f'data-quick>Book a quick 10-min call<span class="vh"> (opens a calendar)</span></a>',
        }
    return {  # no 10-minute event yet: the 30-minute call on this page, and it says so
        '{{QUICK_ASK}}': 'Want to figure out how to optimize this in your routine? That’s what the free call is for.',
        '{{QUICK_STEP}}': 'A free call to find where it slots in',
        '{{QUICK_CALL}}': '<a class="btn q-go" href="#consult">Book a free call</a>',
    }


def bestsellers():
    path = os.path.join(ROOT, 'bestsellers.csv')
    if not os.path.exists(path):
        return []
    return [r for r in csv.DictReader(open(path, newline='')) if r.get('product')]


def main():
    global RECUT
    RECUT = not os.path.exists(STAMP) or open(STAMP).read().strip() != cut_version()
    export = bool(DEMO) or PLUS  # a copy of the site: it photographs nothing and writes no cut stamp
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'share-links.csv'), newline='')))
    os.makedirs(ASSETS, exist_ok=True)
    products = []
    for r in rows:
        p = describe(r)
        src = os.path.join(PHOTOS, r['photo']) if r['photo'] else ''
        studio = os.path.join(STUDIO, slug(r['product']) + '.webp')
        if os.path.exists(studio):
            fn = slug(r['product']) + '.webp'
            if not export:
                shutil.copyfile(studio, os.path.join(ASSETS, fn))
            p['img'] = 'assets/products/' + fn
            p['studio'] = True
            products.append(p)
            continue
        if src and os.path.exists(src):
            fn = slug(r['product']) + os.path.splitext(src)[1].lower()
            if not export:
                normalize(src, os.path.join(ASSETS, fn))
            p['img'] = 'assets/products/' + fn
        else:
            p['img'] = ''
        products.append(p)
    by = {p['product']: p for p in products}
    missing = sorted(set(FAMILIES) - set(TAGLINES))
    if missing:
        raise SystemExit(f'TAGLINES: no line for {missing}')
    for k, (src, chips) in CARD_FACTS.items():
        if k not in by:
            raise SystemExit(f'CARD_FACTS: no such product {k!r}')
        if not src.startswith(AMWAY) or not 2 <= len(chips) <= 4 or any('|' in c for c in chips):
            raise SystemExit(f'CARD_FACTS[{k!r}]: needs its amway.com source and 2-4 chips')
    for n in FEATURED + [t[3] for t in GOAL_TILES]:
        assert n in by, f'Missing product in CSV: {n}'

    cat_of = {}  # each product's home shelf, for its tag: on two shelves, the later one wins
    for slug_, name, tag, heading, fams in CATEGORIES:
        for pr in products:
            if family(pr['product']) in fams:
                cat_of[pr['product']] = slug_
    on_shelf = lambda pr, fams: family(pr['product']) in fams  # what a shelf page lists: its own list, whole
    counts = {c[0]: sum(1 for pr in products if on_shelf(pr, c[4])) for c in CATEGORIES}
    names = {c[0]: c[1] for c in CATEGORIES}

    def card_data(pr):
        """What the product card (#pcard) shows for a pack or a tile, carried on it as data-*, so there is
        no second copy of TAGLINES and CARD_FACTS: its name, kind, line, facts and sound, and data-try, the
        exact listing name that "Ask for a free sample" writes into the sample form's blank."""
        fam = family(pr['product'])
        facts = CARD_FACTS.get(pr['product'], ('', []))[1]
        return (f'data-name="{esc(pr["name"])}" data-kind="{esc(pr["desc"])}" data-line="{esc(TAGLINES[fam])}" '
                f'data-facts="{esc("|".join(facts))}" data-sfx="{CARD_SOUND.get(fam, "chime")}" data-try="{esc(pr["product"])}"')

    def card(pr, i=0, extra='', shelves=False):
        """A product tile: a link to its Amway page, which _script.html turns into the way to its product
        card. The homepage grid's tiles also list every shelf they are on (data-shelves), for the sample
        form's "Pick from the shelves"."""
        u = esc(pr['share_link'])
        tag = names.get(cat_of.get(pr['product']), 'Wellness')
        on = (' data-shelves="' + ' '.join(c[0] for c in CATEGORIES if on_shelf(pr, c[4])) + '"') if shelves else ''
        return (f'        <li class="card grow" style="--d:{i % 4}" data-cat="{cat_of.get(pr["product"], "")}"{extra}>'
                f'<a class="card-link" href="{u}" target="_blank" rel="noopener" {card_data(pr)}{on}>{shot(pr)}'
                f'<p class="p-tag">{tag}</p><h3 class="p-name">{esc(pr["name"])}</h3>'
                f'<p class="p-desc">{esc(pr["desc"])}</p><span class="vh">Buy on Amway (opens in a new tab)</span></a></li>')

    def cat_rows(only=None):
        out_ = []
        for slug_, name, tag, heading, fams in CATEGORIES:
            if only and slug_ in only:
                continue
            out_.append(
                f'          <li><a class="goal" href="category-{slug_}.html">'
                f'<span class="goal-name">{name}</span><span class="goal-desc">{tag.split(":")[0]}</span>'
                f'<span class="goal-island"><img src="assets/thumbs/{slug_}.webp" alt="" width="440" height="440" loading="lazy"></span></a></li>')
        return '\n'.join(out_)

    def ring_section():
        isles = []
        for i, (slug_, name, tag, heading, fams) in enumerate(CATEGORIES):
            prio = ' fetchpriority="high"' if i < 3 else ' loading="lazy"'
            isles.append(
                f'          <li class="isle" style="--i:{i}"><a href="category-{slug_}.html">'
                f'<span class="isle-art"><img src="assets/islands/{slug_}.webp" alt="" width="760" height="760"{prio}></span>'
                f'<span class="isle-label"><span class="isle-name">{name}</span>'
                f'<span class="isle-note">{SHELF_LINE[slug_]}</span></span></a></li>')
        return ('  <!-- Shelves as a rotating ring; tap one to open it -->\n'
                '  <section class="sec isles-sec" id="goals" aria-labelledby="goals-title">\n'
                '    <div class="wrap">\n'
                '      <div class="sec-head grow"><h2 id="goals-title">What are we <span>maximizing?</span></h2></div>\n'
                '      <div class="archipelago" id="archipelago">\n        <ul class="isles">\n'
                + '\n'.join(isles) +
                '\n        </ul>\n'
                '        <button class="icon-btn isles-toggle" id="isles-toggle" type="button" aria-label="Pause the shelves" hidden>'
                '<svg class="ic" aria-hidden="true"><use href="#i-pause"/></svg></button>\n'
                '      </div>\n'
                '      <p class="isle-caption" id="isle-caption" aria-hidden="true"><span class="isle-name"></span><span class="isle-note"></span></p>\n'
                '    </div>\n  </section>')

    def strip_section():
        tabs, panels = [], []
        for i, (slug_, name, tag, heading, fams) in enumerate(CATEGORIES):
            on = 'true' if i == 0 else 'false'
            prio = ' fetchpriority="high"' if i == 0 else ' loading="lazy"'
            tabs.append(
                f'          <button class="shelf-tab" type="button" role="tab" id="tab-{slug_}" aria-controls="panel-{slug_}" '
                f'aria-selected="{on}" tabindex="{0 if i == 0 else -1}">{name}</button>')
            picks = sorted({pr['name'] for pr in products if on_shelf(pr, fams)})[:3]
            panels.append(
                f'        <div class="shelf-panel" role="tabpanel" id="panel-{slug_}" aria-labelledby="tab-{slug_}"'
                f'{"" if i == 0 else " hidden"}>\n'
                f'          <a class="shelf-link" href="category-{slug_}.html">\n'
                f'            <span class="shelf-art"><img src="assets/shelf/{slug_}.webp" alt="" width="760" height="760"{prio}></span>\n'
                f'            <span class="shelf-copy"><span class="label">{SHELF_LINE[slug_]}</span>'
                f'<span class="shelf-name">{name}</span>'
                f'<span class="shelf-desc">{tag.split(":")[0]}</span>'
                f'<span class="shelf-picks">{esc(" · ".join(picks))}</span>'
                f'<span class="shelf-go">Open the shelf</span></span>\n'
                f'          </a>\n        </div>')
        return ('  <!-- Shelves as a goal strip: one tab each, one pack per goal -->\n'
                '  <section class="sec shelves-sec" id="goals" aria-labelledby="goals-title">\n'
                '    <div class="wrap">\n'
                '      <div class="sec-head grow"><h2 id="goals-title">What are we <span>maximizing?</span></h2></div>\n'
                '      <div class="shelf-tabs" role="tablist" aria-label="Shelves">\n'
                + '\n'.join(tabs) +
                '\n      </div>\n      <div class="shelf-panels">\n'
                + '\n'.join(panels) +
                '\n      </div>\n    </div>\n  </section>')

    def case_picks(slug_, fams):
        """A few packs for a compartment: the shelf's own thumbnail first, then one per family, lit
        studio shots before plain cut-outs and otherwise in the order the shelf lists them. A shelf
        with fewer families than that shows what it has."""
        items = [pr for pr in products if on_shelf(pr, fams) and pr['img']]
        first = [pr for pr in items if pr['product'] == CAT_THUMB.get(slug_)]
        rest = sorted(items, key=lambda pr: (not pr.get('studio'), fams.index(family(pr['product']))))
        out_, seen = [], set()
        for pr in first + rest:
            if family(pr['product']) not in seen and len(out_) < CASE_PICKS:
                seen.add(family(pr['product']))
                out_.append(pr)
        for pr in rest:  # one family only: its other packs, so the compartment is not a lone tub
            if len(out_) < 2 and pr not in out_:
                out_.append(pr)
        return out_

    def pack_link(pr, label):
        """A pack in a compartment: a link straight to its Amway page, carrying what its product card
        shows. With script _script.html turns it into a button that opens the card (#pcard); without,
        it stays the link. The card's words and facts ride on it, so there is no second copy of them."""
        named = '' if label == pr['name'] else f'<span class="vh">{esc(pr["name"])}, </span>'
        return (f'<a class="bay-go" href="{esc(pr["share_link"])}" target="_blank" rel="noopener" {card_data(pr)}>'
                f'<img src="{pr["img"]}" alt="" width="600" height="600" loading="lazy" decoding="async">'
                f'{named}<span>{esc(label)}</span><span class="vh">, buy on Amway (opens in a new tab)</span></a>')

    def case_section():
        bays = []
        for i, (slug_, name, tag, heading, fams) in enumerate(CATEGORIES):
            packs = case_picks(slug_, fams)
            names_ = [pr['name'] for pr in packs]
            cells = '\n'.join(
                f'                <li class="bay-pack" style="--k:{j}">{pack_link(pr, pr["name"] if names_.count(pr["name"]) == 1 else pr["desc"].split(" · ")[-1])}</li>'
                for j, pr in enumerate(packs))
            bays.append(
                f'          <li class="bay" style="--i:{i}">\n'
                f'            <button class="bay-lid" type="button" id="lid-{slug_}" aria-expanded="false" aria-controls="bay-{slug_}">'
                f'<span class="lid" aria-hidden="true"></span>'
                f'<span class="bay-name">{name}</span><span class="vh">, </span><span class="bay-note">{SHELF_LINE[slug_]}</span></button>\n'
                f'            <div class="bay-well"><div class="bay-in" id="bay-{slug_}" role="region" aria-labelledby="lid-{slug_}" hidden>\n'
                f'              <ul class="bay-packs">\n{cells}\n              </ul>\n'
                f'              <a class="bay-all" href="category-{slug_}.html">See all {name}'
                f'<svg class="ic ic-sm" aria-hidden="true"><use href="#i-arrow"/></svg></a>\n'
                f'            </div></div>\n'
                f'          </li>')
        return ('  <!-- Shelves as the stack case: one compartment per shelf, all seven labelled at once. A lid is\n'
                '       a real button; it opens onto a few of that shelf\'s packs and a link to the shelf, one\n'
                '       compartment at a time (_script.html). Without script every compartment stands open. -->\n'
                '  <section class="sec case-sec" id="goals" aria-labelledby="goals-title">\n'
                '    <div class="wrap">\n'
                '      <div class="sec-head grow"><h2 id="goals-title">What are we <span>maximizing?</span></h2></div>\n'
                '      <div class="case grow" id="case">\n        <ul class="case-bays">\n'
                + '\n'.join(bays) +
                '\n        </ul>\n      </div>\n    </div>\n'
                + card_dialog() +
                '  </section>')

    def card_dialog(home=''):
        """The product card every pack and product tile opens (_script.html fills it from the one it opened
        from): the case's and the rack's packs, the homepage grid, Trending, and every shelf page's tiles.
        A modal <dialog>: without script, or without dialog support, nothing opens it and it never shows.
        "Ask for a free sample" goes to the sample form: on the homepage (home '') in place, on a shelf page
        (home 'homepage.html') by the homepage's ?try= link, the exact product name in it."""
        return ('    <dialog class="pcard" id="pcard" aria-labelledby="pcard-name" aria-describedby="pcard-line">\n'
                '      <div class="pcard-in">\n'
                '        <button class="icon-btn pcard-x" type="button" aria-label="Close"><svg class="ic" aria-hidden="true"><use href="#i-close"/></svg></button>\n'
                '        <div class="pcard-art"><img id="pcard-img" alt="" width="600" height="600"></div>\n'
                '        <div class="pcard-copy">\n'
                '          <p class="pcard-kind" id="pcard-kind"></p>\n'
                '          <h3 class="pcard-name" id="pcard-name"></h3>\n'
                '          <p class="pcard-line" id="pcard-line"></p>\n'
                '          <ul class="pcard-facts" id="pcard-facts" aria-label="Quick facts"></ul>\n'
                # DRAFT-COPY: "Buy on Amway", never "Add to cart": it opens the product's own page through Peter's
                # share link, and the visitor puts it in the cart there (Amway has no add-to-cart link)
                '          <div class="pcard-acts"><a class="btn pcard-buy" id="pcard-buy" href="#" target="_blank" rel="noopener">Buy on Amway'
                '<span class="vh"> (opens in a new tab)</span></a>'
                # DRAFT-COPY. The buttons say "Ask for a free sample"; the sample section's heading and the game
                # plan's step 02 say "Request a free sample", Peter's own words. That phrase is also his business
                # partner's button, and Peter has said that is fine (2026-10-01), so neither is a mistake to fix.
                f'<a class="btn btn-line pcard-try" id="pcard-try" href="{home}#sample"'
                + (f' data-home="{home}"' if home else '') + '>Ask for a free sample</a>'
                # DRAFT-COPY: the script names the plate after it and reads "On your bar" once it is on
                + ('<button class="btn btn-line pcard-load" id="pcard-load" type="button" hidden>'
                   '<span class="pl-t">Load this plate</span><span class="vh pl-cat"></span></button>' if SHELF_VIEW == 'bar' and not home else '')
                + '</div>\n'
                '        </div>\n'
                '      </div>\n'
                '    </dialog>\n')

    def stack_dialog():
        """"Take my stack to Amway" (#sa): the panel under "Build yours." that turns the plates on the
        visitor's bar into an order they can actually place. The shell only — _script.html fills the
        list from the rack's own panels, so the products offered here are the picks the rack already
        shows and there is no second copy of them, and a tenth shelf needs nothing here. A modal
        <dialog>: without script, or without dialog support, nothing opens it and the button that
        would is hidden. All of it is DRAFT-COPY."""
        return ('    <!-- DRAFT-COPY -->\n'
                '    <dialog class="sa" id="sa" aria-labelledby="sa-title">\n'
                '      <div class="sa-in">\n'
                '        <button class="icon-btn sa-x" type="button" aria-label="Close"><svg class="ic" aria-hidden="true"><use href="#i-close"/></svg></button>\n'
                '        <h2 class="sa-title" id="sa-title" tabindex="-1">Your stack on Amway</h2>\n'
                '        <p class="sa-lead" id="sa-lead"></p>\n'
                '        <p class="sa-why">When you order through my link, Amway credits the order to me \u2014 that\u2019s '
                'how I get paid. You pay Amway\u2019s normal price, and there\u2019s no code to enter.</p>\n'
                '        <ul class="sa-list" id="sa-list"></ul>\n'
                '        <div class="sa-acts"><button class="btn sa-start" id="sa-start" type="button">'
                'Open the first one on Amway<span class="vh"> (opens in a new tab)</span></button>'
                '<button class="btn btn-line sa-again" id="sa-again" type="button" hidden>Start over</button>'
                '<button class="btn btn-line sa-done" id="sa-done" type="button">Close</button></div>\n'
                '      </div>\n'
                '    </dialog>\n'
                '    <!-- /DRAFT-COPY -->\n')

    def rack_section():
        """The plate rack: the seven shelves as seven plates, all on show, front on. A plate is a button
        (aria-pressed: its panel is the one showing); its panel has a few of the shelf's packs (each opens
        the product card, as the case's do), "Load this plate" and a link to the shelf. The plates and the
        panels share one wrapping row (the list is display:contents), so the script can set the open
        panel in under its own plate's row with `order` alone: one copy of each, ids and aria untouched.
        Without script every panel stands open under the rack and nothing loads."""
        plates, panels = [], []
        for i, (slug_, name, tag, heading, fams) in enumerate(CATEGORIES):
            col, rank = PLATES[slug_]
            plates.append(
                f'          <li><button class="rk-plate" type="button" id="rk-{slug_}" aria-pressed="false" aria-controls="rk-p-{slug_}" '
                f'data-cat="{slug_}" data-rank="{rank}" style="--c:{col};--t:{plate_ink(col)}">'
                f'<span class="rk-disc" aria-hidden="true"><span class="rk-hole"></span></span>'
                f'<span class="rk-name">{name}</span><span class="rk-line" aria-hidden="true">{SHELF_LINE[slug_]}</span>'
                f'<span class="rk-on">On the bar</span></button></li>')
            packs = case_picks(slug_, fams)
            names_ = [pr['name'] for pr in packs]
            cells = '\n'.join(
                f'              <li class="bay-pack" style="--k:{j}">{pack_link(pr, pr["name"] if names_.count(pr["name"]) == 1 else pr["desc"].split(" · ")[-1])}</li>'
                for j, pr in enumerate(packs))
            panels.append(
                f'        <div class="rk-panel" id="rk-p-{slug_}" role="region" aria-labelledby="rk-t-{slug_}" style="--c:{col}" hidden>\n'
                f'          <div class="rk-head"><h3 class="rk-title" id="rk-t-{slug_}">{name}</h3><p class="rk-sub">{SHELF_LINE[slug_]}</p></div>\n'
                f'          <ul class="bay-packs rk-packs">\n{cells}\n          </ul>\n'
                f'          <div class="rk-acts"><button class="btn rk-load" type="button" aria-pressed="false" data-cat="{slug_}" hidden>Load this plate</button>'
                f'<a class="bay-all rk-all" href="category-{slug_}.html">See all {name}<svg class="ic ic-sm" aria-hidden="true"><use href="#i-arrow"/></svg></a>'
                # the way on to an order, from the rack itself: the same panel as "Build yours."'s button.
                # Hidden until there is a stack and the script can open that panel (_script.html)
                f'<!-- DRAFT-COPY --><button class="rk-amway" type="button" aria-haspopup="dialog" hidden>Take my stack to Amway'
                f'<svg class="ic ic-sm" aria-hidden="true"><use href="#i-arrow"/></svg></button><!-- /DRAFT-COPY --></div>\n'
                f'        </div>')
        return ('  <!-- Shelves as a plate rack: one plate per shelf, all seven at once, nothing moving on its own.\n'
                '       A plate is a button that shows its shelf\'s panel; "Load this plate" puts it on the visitor\'s\n'
                '       bar, pinned under the masthead (_script.html). Without script every panel stands open. -->\n'
                '  <section class="sec rack-sec" id="goals" aria-labelledby="goals-title">\n'
                '    <div class="wrap">\n'
                '      <div class="sec-head grow"><div><h2 class="hl-2" id="goals-title"><span class="hl-lead">What are we</span> <span class="hl-k">maximizing?</span></h2>'
                + RACK_GUIDE + '</div></div>\n'
                '      <div class="rack grow" id="rack">\n        <ul class="rk-plates" role="list">\n'
                + '\n'.join(plates) +
                '\n        </ul>\n' + '\n'.join(panels) + '\n      </div>\n    </div>\n'
                + card_dialog() +
                '  </section>')

    shelves = {'ring': ring_section, 'strip': strip_section, 'case': case_section, 'bar': rack_section}[SHELF_VIEW]()
    BAR = SHELF_VIEW == 'bar'
    # the story's caption strip links to Peter's shelves, and each pack on its shelf names the same
    # one (data-cat); the bar theme loads his plates in that order
    story_src = open(SRC).read()
    story_cats = re.findall(r'class="tlink st-go" href="category-([a-z-]+)\.html"', story_src)
    # each shelf's first pack in the story (the one "That's my stack" shows beside its plate)
    story_pack = {}
    for m in re.finditer(r'<span class="st-pack" data-cat="([a-z-]+)"[^>]*>\s*<span class="st-shade"></span><img src="([^"]+)"', story_src):
        story_pack.setdefault(m.group(1), m.group(2))
    pack_cats = list(dict.fromkeys(re.findall(r'<span class="st-pack" data-cat="([a-z-]+)"', story_src)))
    if BAR and story_cats != PETER:
        raise SystemExit(f"PETER: the story's caption strip links {story_cats}, not {PETER}")
    if BAR and pack_cats != PETER:
        raise SystemExit(f"PETER: the story's packs land for {pack_cats}, not {PETER}")
    if BAR and sorted(story_pack) != sorted(PETER):
        raise SystemExit(f"PETER: found a pack picture for {sorted(story_pack)}, not for each of {PETER}")
    bar_bits = {k: '' for k in ('{{HTML_CLASS}}', '{{PIN}}', '{{ARC_BAR}}', '{{MYSTACK}}')}
    if BAR:
        pn = [(c, names[c]) for c in PETER]
        caps = ''.join(f'<span class="lbc lbc-p" data-n="{n}">Peter’s<span class="lbc-lg"> stack</span> · {n} of {len(PETER)}</span>' for n in range(len(PETER) + 1))   # a phone's one-row strip drops "stack"
        news = ''.join(f'<span class="lbc lbc-pnew" data-cat="{c}">+ {n}</span>' for c, n in pn)
        bar_bits.update({
            '{{HTML_CLASS}}': ' class="t-bar"',
            # the pinned bar: the visitor's stack, or Peter's through #story; the script shows it once the hero has gone
            '{{PIN}}': ('<div class="lbpin" id="lbpin" aria-hidden="true"><div class="wrap lbpin-in">'
                        '<div class="lbpin-bars bbx">' + barbell('bb-you') + barbell('bb-peter') + '</div>'
                        '<p class="lbpin-cap"><span class="lbc-set lbc-yset"><span class="lbc-who"><span class="lbc lbc-you"></span></span>'
                        '<span class="lbc-new"><span class="lbc lbc-ynew"></span></span></span>'
                        '<span class="lbc-set lbc-pset"><span class="lbc-who">' + caps + '</span><span class="lbc-new">' + news + '</span></span></p></div></div>'),
            '{{ARC_BAR}}': '<div class="bbx">' + barbell('bb-arc', PETER) + '</div>',
            '{{MYSTACK}}': ('  <!-- After the story: the stack his story loaded, drawn loaded, with its key, and the two ways on -->\n'
                            '  <section class="sec dark mys" id="my-stack" aria-labelledby="mys-title">\n    <div class="wrap mys-in">\n'
                            '      <h2 class="grow hl-2 hl-dk" id="mys-title"><span class="hl-lead">That’s</span> <span class="hl-k">my stack.</span></h2>\n'
                            '      <div class="mys-bar bbx grow" style="--d:1">' + barbell('bb-dk bb-big', PETER) + '</div>\n'
                            '      <ul class="mys-key grow" style="--d:2" aria-label="The plates on it">'
                            + ''.join(f'<li><span class="mys-th"><img src="{story_pack[c]}" alt="" loading="lazy" decoding="async" width="96" height="96"></span>'
                                      f'<span class="mys-n"><i style="--c:{PLATES[c][0]}"></i>{n}</span></li>' for c, n in pn) + '</ul>\n'
                            '      <p class="mys-build grow hl-3d hl-dk" style="--d:2">Build yours.</p>\n'
                            # the visitor's stack beside his, from the saved stack (_script.html fills it); none yet, an
                            # invitation to the rack. Without script there is no stack to show, so none of it shows.
                            '      <!-- DRAFT-COPY --><div class="mys-you grow" id="mys-you" style="--d:2">\n'
                            '        <div class="mys-has" hidden><p class="mys-cap"><span class="mys-n">Your stack</span>'
                            '<a class="mys-edit" href="#goals">Change it</a></p>\n'
                            '        <div class="mys-ybar bbx">' + barbell('bb-dk bb-you') + '</div>\n'
                            '        <ul class="mys-key mys-ykey" aria-label="The plates on yours"></ul>\n'
                            # the way to actually buy it. Hidden until the script (and <dialog>) can run it, so
                            # a no-JS visitor — who has no stack either — is never offered it
                            '        <p class="mys-amway"><button class="btn sa-go" id="sa-go" type="button" aria-haspopup="dialog" hidden>Take my stack to Amway</button></p></div>\n'
                            '        <p class="mys-none">Nothing on your bar yet. <a href="#goals">Load a plate or two</a> and bring them along.</p>\n'
                            '      </div><!-- /DRAFT-COPY -->\n'
                            '      <!-- DRAFT-COPY --><p class="mys-sub grow" style="--d:3">Fifteen minutes, free. Your macros, what you already take, and the smallest stack that moves your goal.</p>\n'
                            '      <div class="mys-acts grow" style="--d:3"><a class="btn" href="#macros">Work out your macros</a>'
                            '<a class="btn btn-line" href="#consult">Book a free call</a></div>\n'
                            '    </div>\n  </section>\n'
                            + stack_dialog()),
        })
    # the story's stack is the same case in miniature: the same seven compartments, in the same order,
    # empty until the story's packs tuck into them (_script.html measures them; nothing here moves)
    case_strip = '' if BAR else ('<div class="st-row st-case" aria-hidden="true"><span class="stc-body">'
                  + ''.join(f'<span class="stc-bay" data-cat="{s}"><span class="stc-well"></span>'
                            f'<span class="stc-name">{n}</span></span>' for s, n, *_ in CATEGORIES)
                  + '</span></div>')   # the bar theme's pinned bar is the story's stack instead
    order = sorted(products, key=lambda pr: pr['name'].lower())
    grid = [card(pr, i, shelves=True) for i, pr in enumerate(order)]

    part = lambda n: open(os.path.join(ROOT, 'site-src', n)).read()
    style, header, footer, dialogs, script, icons = (part('style.css'), part('_header.html'), part('_footer.html'),
                                                     part('_dialogs.html'), part('_script.html'), part('_icons.html'))
    intro = part('_intro.html')  # the opening curtain: homepage only, so it is not in `shared`
    style_hash = hashlib.sha1(style.encode()).hexdigest()[:8]  # bust the cache when the css moves
    if PLUS:  # the copy links the one stylesheet at the repo root, so there can never be two of it
        style_href = '../style.css?v=' + style_hash
    else:
        style_file = os.path.join(DEMO, DEMO_STYLE) if DEMO else STYLE_OUT
        if DEMO:
            open(style_file, 'w').write(style)
        else:
            write_plain('style.css', style)  # served once and cached, instead of inlined into every page
        style_href = os.path.basename(style_file) + '?v=' + style_hash
    # the menu sheet lists every shelf; it follows {{DIALOGS}} in this dict so it fills the menu once it is in
    menu_shelves = '\n'.join(f'        <li><a href="category-{s}.html">{n}</a></li>' for s, n, *_ in CATEGORIES)
    shared = {'{{STYLE}}': style_href, '{{FOOTER}}': footer, '{{DIALOGS}}': dialogs, '{{MENU_SHELVES}}': menu_shelves,
              '{{CCRX}}': ccrx_block(),  # after {{FOOTER}}, which is where the placeholder sits
              '{{SCRIPT}}': script,
              '{{ICONS}}': icons, '{{TOTAL}}': str(len(products)),
              '{{TOTAL_PRODUCTS}}': plural(len(products), 'product', zero='products'), '{{CONSULT_URL}}': CONSULT_URL,
              '{{BASE}}': BASE}
    # "Pick from the shelves", beside the sample form's product blank: the shelves as small plates in their
    # rack colours; the script lists the one tapped's products from the homepage grid's tiles (data-shelves,
    # card()). Hidden until the script shows it, so without script the blank is the whole question. DRAFT-COPY
    sample_picker = ('<div class="s-pick" id="s-pick" hidden>\n'
                     '            <button class="s-pick-go" type="button" id="s-pick-go" aria-expanded="false" aria-controls="s-picker">'
                     '<span class="s-pick-pl" aria-hidden="true"></span>Pick from the shelves</button>\n'
                     '            <div class="s-picker" id="s-picker" hidden>\n'
                     '              <div class="sp-view" id="sp-shelves"><p class="sp-t" id="sp-shelves-t">Pick a shelf</p>\n'
                     '                <ul class="sp-plates" aria-labelledby="sp-shelves-t">'
                     + ''.join(f'<li><button class="sp-plate" type="button" data-cat="{s}" style="--c:{PLATES.get(s, ("#6B5646", 0))[0]}">'
                               f'<span class="sp-disc" aria-hidden="true"><span class="sp-hole"></span></span>'
                               f'<span class="sp-name">{n}</span></button></li>' for s, n, *_ in CATEGORIES) +
                     '</ul></div>\n'
                     '              <div class="sp-view" id="sp-list" hidden><div class="sp-head">'
                     '<button class="sp-back" type="button" id="sp-back"><svg class="ic ic-sm" aria-hidden="true" focusable="false"><use href="#i-back"/></svg>All shelves</button>'
                     '<p class="sp-t" id="sp-list-t"></p></div>\n'
                     '                <ul class="sp-items" id="sp-items" aria-labelledby="sp-list-t"></ul></div>\n'
                     '            </div>\n          </div>')
    # what the sample form's "What would you like to try?" suggests: every family, by the name its cards carry
    sample_list = '\n'.join(f'          <option value="{esc(n)}"></option>'
                            for n in sorted({pr['name'] for pr in products}, key=str.lower))

    if not export:
        os.makedirs(CUTS, exist_ok=True)
    podium = []
    # each of the three carries its family's TAGLINES line (.p-why), the same DRAFT-COPY its product card
    # shows, so the band says why a pack is worth a look and not only what it is; no new claims here.
    # the podium is built on every build, shown or not: it is what checks bestsellers.csv against
    # share-links.csv. TRENDING (top of this file) only decides whether the band goes on the page.
    for i, r in enumerate(bestsellers()[:3]):
        pr = dict(by.get(r['product']) or {})
        if not pr:
            raise SystemExit(f"bestsellers.csv: no such product {r['product']!r}")
        photo = next((row['photo'] for row in rows if row['product'] == r['product']), '')
        if photo and os.path.exists(os.path.join(PHOTOS, photo)):  # transparent cut-out for the dark band
            fn = slug(r['product']) + '.webp'
            if not export:
                normalize(os.path.join(PHOTOS, photo), os.path.join(CUTS, fn))
            pr['img'] = 'assets/cutouts/' + fn
            pr['studio'] = False
        units = (r.get('units_this_week') or '').strip()
        count = (f'<p class="pod-count"><span class="pod-num" data-count="{units}">0</span> '
                 f'bought this week</p>') if units.isdigit() else ''
        podium.append(
            f'        <li class="pod pod-{i + 1}"><a class="card-link" href="{esc(pr["share_link"])}" target="_blank" rel="noopener" {card_data(pr)}>'
            f'<span class="pod-rank" aria-hidden="true">0{i + 1}</span>'
            f'{shot(pr, lazy=False)}<p class="p-tag">{names.get(cat_of.get(pr["product"]), "Wellness")}</p>'
            f'<h3 class="p-name">{esc(pr["name"])}</h3><p class="p-desc">{esc(pr["desc"])}</p>'
            f'<p class="p-why">{esc(TAGLINES[family(pr["product"])])}</p>{count}'
            f'<span class="vh">Buy on Amway (opens in a new tab)</span></a></li>')

    # The band itself: {{TRENDING}} in homepage.template.html, and '' unless TRENDING (top of this
    # file) is True — one switch, and the section comes back exactly where and as it was.
    trending = (('''  <!-- 4. Trending: the week's three best sellers, each with its family's TAGLINES line, as
       three compact cards on the page's own field, all three in view at every width. It sits
       between the calculator (#macros) and Peter's story (#story). Switched by TRENDING in
       build_homepage.py; the whole section is built there. -->
  <section class="sec podium-sec no-pour" id="trending" aria-labelledby="trending-title">
    <div class="wrap">
      <div class="sec-head grow"><h2 id="trending-title">Trending now</h2></div>
      <ul class="podium">
'''
                 + '\n'.join(podium) + '''
      </ul>
    </div>
  </section>
''') if TRENDING else '')

    page_name = DEMO_PAGE if DEMO else 'homepage.html'
    # the CCRX copy is findable on purpose (Peter wants it indexed), so it is NOT noindexed like a
    # demo; it only needs a canonical of its own. plus_links() moves that to PLUS_DIR/ with the rest.
    head_extra = (f'<meta name="robots" content="noindex">\n<link rel="canonical" href="{BASE}{DEMO_PAGE}">\n'
                  if DEMO else f'<link rel="canonical" href="{BASE}homepage.html">\n' if PLUS else '')
    out = open(SRC).read()
    for k, v in dict(shared, **{'{{HEADER}}': header.replace('{{HOME}}', ''), '{{HOME}}': '',
                                '{{HEAD_EXTRA}}': head_extra,
                                '{{PAGE_URL}}': BASE + page_name, '{{INTRO}}': intro,
                                '{{GOALS}}': cat_rows(),
                                '{{SAMPLE_ENDPOINT}}': SAMPLE_ENDPOINT, '{{SAMPLE_ACTION}}': SAMPLE_ACTION,
                                '{{SAMPLE_NEXT}}': SAMPLE_NEXT.replace('homepage.html', page_name), '{{SAMPLE_PRODUCTS}}': sample_list,
                                '{{SAMPLE_PICKER}}': sample_picker, '{{PCARD}}': '' if SHELF_VIEW in ('bar', 'case') else card_dialog(), **quick_call(), '{{GRID}}': '\n'.join(grid), '{{TRENDING}}': trending, '{{SHELVES}}': shelves,
                                '{{CASE_STRIP}}': case_strip,
                                **bar_bits}).items():
        out = out.replace(k, v)
    left = sorted(set(re.findall(r'\{\{[A-Z_]+\}\}', out)))
    if left:
        raise SystemExit(f'unfilled placeholders in the homepage: {left}')
    plus_pages = {}
    if DEMO:
        out = demo_links(out)
        open(os.path.join(DEMO, DEMO_PAGE), 'w').write(out)
        demo_pages = {DEMO_PAGE: out}
    elif PLUS:
        plus_pages['homepage.html'] = write_plus('homepage.html', out)
    else:
        write_plain('homepage.html', out)

    cat_tpl = open(os.path.join(ROOT, 'site-src', 'category.template.html')).read()
    for slug_, name, tag, heading, fams in CATEGORIES:
        items = [pr for pr in products if on_shelf(pr, fams)]
        items.sort(key=lambda pr: (pr['name'].lower(), pr['desc'].lower()))
        carousel = ''
        if slug_ in CAROUSELS:
            fam, chead, cline = CAROUSELS[slug_]
            flav = [pr for pr in items if family(pr['product']) == fam]
            items = [pr for pr in items if pr not in flav]
            slides = '\n'.join(
                f'          <li class="slide"><a class="card-link" href="{esc(pr["share_link"])}" target="_blank" rel="noopener" {card_data(pr)}>'
                f'{shot(pr)}<h3 class="p-name">{esc(pr["desc"].split(" · ")[-1])}</h3>'
                f'<span class="vh">{esc(pr["name"])}, buy on Amway (opens in a new tab)</span></a></li>' for pr in flav)
            carousel = f'''  <!-- Flavor carousel: glides on its own, arrows or swipe to take over -->
  <section class="sec carousel-sec" aria-labelledby="flavors-title">
    <div class="wrap">
      <div class="sec-head grow"><h2 id="flavors-title">{chead}</h2>
        <div class="car-nav"><button class="icon-btn" type="button" data-car="-1" aria-label="Previous flavor"><svg class="ic" aria-hidden="true"><use href="#i-back"/></svg></button><button class="icon-btn" type="button" data-car="1" aria-label="Next flavor"><svg class="ic" aria-hidden="true"><use href="#i-arrow"/></svg></button></div>
      </div>
      <ul class="carousel" id="carousel" data-autoplay>
{slides}
      </ul>
    </div>
  </section>

'''
        cgrid = '\n'.join(card(pr, i) for i, pr in enumerate(items))
        page = cat_tpl
        cat_page = f'category-{slug_}{DEMO_SUFFIX}.html' if DEMO else f'category-{slug_}.html'
        for k, v in dict(shared, **{
                '{{HEADER}}': header.replace('{{HOME}}', 'homepage.html'), '{{HOME}}': 'homepage.html',
                '{{HEAD_EXTRA}}': (f'<meta name="robots" content="noindex">\n<link rel="canonical" href="{BASE}{cat_page}">\n'
                                   if DEMO else f'<link rel="canonical" href="{BASE}category-{slug_}.html">\n' if PLUS else ''),
                '{{PAGE_URL}}': BASE + f'category-{slug_}.html',
                '{{SAMPLE_LINK}}': 'homepage.html?try=' + quote(html.unescape(name)) + '#sample',
                '{{CAT_NAME}}': name, '{{CAT_TAG}}': tag, '{{CAT_HEADING}}': heading,
                '{{CAT_COUNT}}': plural(counts[slug_], 'product', zero='No products yet'), '{{CAT_GRID}}': cgrid, '{{CAROUSEL}}': carousel,
                '{{CAT_OTHERS}}': cat_rows(only={slug_}), **hero_media(slug_, name), '{{PCARD}}': card_dialog('homepage.html'),
                '{{CAT_EXTRA}}': SHELF_EXTRA.get(slug_, lambda: '')()}).items():
            page = page.replace(k, v)
        if DEMO:  # its own links, og:url included, name the demo copies (demo_links)
            page = demo_links(page)
            demo_pages[cat_page] = page
            open(os.path.join(DEMO, cat_page), 'w').write(page)
            continue
        if PLUS:
            plus_pages[cat_page] = write_plus(cat_page, page)
            continue
        write_plain(f'category-{slug_}.html', page)

    # about.html: who we are, then what changed, then the numbers, then the way on. Its own page off the
    # menu instead of a band at the end of the homepage, because all of it there was too much in one thing
    # (Peter, 2026-09-28). Generated like the shelf pages: never hand-edit about.html. It needs no rack,
    # no story stage and no macro calculator, and the shared script leaves out what a page does not have.
    about_page = f'about{DEMO_SUFFIX}.html' if DEMO else 'about.html'
    page = open(os.path.join(ROOT, 'site-src', 'about.template.html')).read()
    for k, v in dict(shared, **{
            '{{HEADER}}': header.replace('{{HOME}}', 'homepage.html'), '{{HOME}}': 'homepage.html',
            '{{HEAD_EXTRA}}': ((f'<meta name="robots" content="noindex">\n<link rel="canonical" href="{BASE}{about_page}">\n')
                               if DEMO else f'<link rel="canonical" href="{BASE}about.html">\n'),
            '{{PAGE_URL}}': BASE + 'about.html',
            '{{ABOUT_TAG}}': ABOUT_TAG, '{{ABOUT_SUB}}': ABOUT_SUB,
            '{{ABOUT_PORTRAITS}}': about_portraits(),
            '{{ABOUT_HIS}}': peter_text(), '{{ABOUT_HERS}}': her_text(None, 3, 'her-title', her_says('{n}', 'My wife')),
            '{{ABOUT_PROOF}}': proof_wall(), '{{ABOUT_DEXA}}': dexa_cards(),
            '{{PCARD}}': ''}).items():
        page = page.replace(k, v)
    left = sorted(set(re.findall(r'\{\{[A-Z_]+\}\}', page)))
    if left:
        raise SystemExit(f'unfilled placeholders in about.html: {left}')
    if DEMO:
        page = demo_links(page)
        demo_pages[about_page] = page
        open(os.path.join(DEMO, about_page), 'w').write(page)
    elif PLUS:
        plus_pages[about_page] = write_plus(about_page, page)
    else:
        write_plain('about.html', page)

    if DEMO:
        demo_report(demo_pages, style)
        return
    if PLUS:
        # the copy is a folder, so it needs two files of its own: a directory index, so that
        # .../RAW/plus/ opens the copy's homepage, and a manifest whose start_url ('.') resolves
        # inside the copy, so an installed shortcut cannot land a visitor on the plain site.
        open(plus_path('index.html'), 'w').write(open(os.path.join(ROOT, 'index.html')).read())
        man = open(os.path.join(ROOT, 'site.webmanifest')).read().replace('"src": "assets/', '"src": "../assets/')
        open(plus_path('site.webmanifest'), 'w').write(man)
        plus_report(plus_pages)
        return
    open(STAMP, 'w').write(cut_version())  # last, so a crash leaves the old stamp and the next run re-cuts
    guard_root()  # belt and braces: the files at the root that this build did not write
    print(f'{len(products)} products ({sum(1 for pr in products if pr["img"])} with photos) -> {OUT}')
    print('categories', counts, 'uncategorised', [pr['product'] for pr in products if pr['product'] not in cat_of])


def ccrx_block():
    """The CCRX route: the one thing the two published copies differ by (see CCRX at the top).

    Switch off -> the empty string, so the plain pages are byte-for-byte what they were before any
    of this existed. Switch on -> this one link, in the footer of every page of the copy.

    DRAFT-COPY. This is a placeholder, not Peter's words, and it makes no claim about what the
    products do: it names the two things CCRX sells and links his referral address. Peter's real
    block (his wording, and wherever on the page he wants it) replaces the return below and nothing
    else in the build has to change; if it wants a place of its own rather than the footer, put a
    second {{CCRX}} in the template it belongs to and give this one a sibling.
    """
    if not CCRX:
        return ''
    return ('\n        <!-- DRAFT-COPY: placeholder for the CCRX route. Peter has not approved copy for it;\n'
            '             it is here so the two builds genuinely differ and the guard has a link to catch. -->\n'
            f'        <a href="{CCRX_URL}" target="_blank" rel="noopener">Prescription peptides and bloodwork'
            '<span class="vh"> (opens in a new tab)</span></a>')


def plus_path(name):
    """A file of the CCRX copy, under PLUS_DIR/ in the repo."""
    if not re.fullmatch(r'[a-z0-9-]+', PLUS_DIR):  # the copy's pages link ../assets/ and ../style.css,
        raise SystemExit(f'PLUS_DIR must be one folder name, not {PLUS_DIR!r}')  # so it is one level down
    d = os.path.join(ROOT, PLUS_DIR)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def write_plus(name, page):
    """Write one page of the CCRX copy, with its links pointed inside the copy first."""
    page = plus_links(page)
    open(plus_path(name), 'w').write(page)
    return page


def plus_links(page):
    """Keep the CCRX copy's pages inside the CCRX copy, the way demo_links keeps a demo inside itself.

    The copy's pages carry the SAME file names as the plain site's, one folder down, so every
    relative link between them (homepage.html, about.html, category-*.html, '#top', '?try=') already
    resolves inside PLUS_DIR/ and needs nothing done to it. Two kinds of reference do need work:
      * an ABSOLUTE link to a page of the site -- og:url, the canonical, the sample form's _next --
        which would otherwise send a visitor of the copy back to the plain site;
      * a RELATIVE reference to a file the two copies share and only the root has: assets/ and the
        root style.css. Those are one folder up. The lookbehind leaves alone anything already inside
        a URL (BASE + 'assets/...' for og:image, 'assets.calendly.com/assets/...'), which is right:
        those resolve on their own.
    Nothing here renames a page, so the copy's URLs read like the plain site's with PLUS_DIR/ in
    front, and its pages can be diffed against the plain ones line for line.
    """
    shelves = '|'.join(re.escape(c[0]) for c in CATEGORIES)
    pages = rf'(?:homepage|about|category-(?:{shelves}))\.html'
    page = re.sub(rf'({re.escape(BASE)})({pages})', rf'\1{PLUS_DIR}/\2', page)
    return re.sub(r'(?<![\w./-])assets/', '../assets/', page)


def guard(name, text, on_disk=False):
    """THE GUARD. The plain site must never carry the link to Peter's CCRX storefront.

    Peter, 2026-10-01: "The only thing to avoid is having the specific uh, crystal clear RX website
    built into the other website. ... Actually, even the name crystal clear is fine. Just the link
    itself." So this checks for the HOSTS in CCRX_HOSTS and for nothing else -- the words "CCRX",
    "Avellum Health", "peptide" and "bloodwork" are all free to appear in either copy, and the
    footer's ordering line already names Avellum Health.

    It runs on the way to disk, so a leaked page is never even written, and it is unconditional:
    no flag and no switch skips it. `--ccrx on` puts the link into the plain pass on purpose and
    this is what stops it. If Peter one day decides the plain site SHOULD carry the link, this
    function is the single place that has to be changed, deliberately, by someone reading this.
    """
    hits = [(i, h, line.strip()) for i, line in enumerate(text.splitlines(), 1)
            for h in CCRX_HOSTS if h in line.lower()]
    if not hits:
        return text
    where = '\n'.join(f'!!   {name}:{i}  names {h}\n!!     {ln[:140]}' for i, h, ln in hits)
    what = (f'!! {name} already carries it at the repo root; this build did not write it.'
            if on_disk else f'!! {name} was NOT written.')
    raise SystemExit(
        f'\n!! BUILD STOPPED: the CCRX link leaked into the plain site.\n'
        f'{what} {len(hits)} occurrence(s):\n{where}\n'
        f'!! Only the copy under {PLUS_DIR}/ may name {" or ".join(CCRX_HOSTS)}; the pages at the\n'
        f'!! repo root are the site Peter sends to anyone, and they must never link it\n'
        f'!! (Peter, 2026-10-01: "Just the link itself.").\n'
        f'!! Put it behind the CCRX switch in {os.path.basename(__file__)} (see ccrx_block), then rebuild.')


def write_plain(name, text):
    """Write one file of the plain site at the repo root -- past the guard, or not at all."""
    guard(name, text)
    open(os.path.join(ROOT, name), 'w').write(text)
    PLAIN_WRITTEN.append(name)
    return text


def guard_root():
    """The same check over every page and stylesheet at the repo root as it now stands on disk, so
    a hand-edited page, a stale generated one or a demo export dropped in beside them is caught too.
    PLUS_DIR/ is a folder of its own and is not read here: it is the copy that is allowed the link."""
    names = sorted(f for f in os.listdir(ROOT)
                   if f.endswith(('.html', '.css', '.webmanifest')) and os.path.isfile(os.path.join(ROOT, f)))
    for f in names:
        guard(f, open(os.path.join(ROOT, f), encoding='utf-8', errors='replace').read(), on_disk=True)
    print(f'guard: no {"/".join(CCRX_HOSTS)} link in the {len(names)} files of the plain site '
          f'({len(PLAIN_WRITTEN)} of them written by this build)')


def plus_report(pages):
    """What the second pass wrote, and the proof that it really differs from the plain site."""
    carries = [n for n, t in pages.items() if any(h in t.lower() for h in CCRX_HOSTS)]
    if CCRX and not carries:
        raise SystemExit(f'{PLUS_DIR}/: CCRX is on but not one page carries the link - the switch did nothing')
    out = sorted(os.listdir(os.path.join(ROOT, PLUS_DIR)))
    print(f'{PLUS_DIR}/: {len(pages)} pages + index.html + site.webmanifest ({len(out)} files), '
          f'CCRX {"on" if CCRX else "off"}, {len(carries)} of them carry the link; '
          f'they link ../style.css and ../assets/')


def demo_links(page):
    """A demo page's links to the homepage and to every shelf, relative or absolute (og:url, the search's
    'homepage.html?q=', a card's '?try=' link), rewritten to name the demo copies beside it."""
    page = re.sub(r'(?<![\w-])homepage\.html', DEMO_PAGE, page)
    page = re.sub(r'(?<![\w-])about\.html', f'about{DEMO_SUFFIX}.html', page)
    shelves = '|'.join(re.escape(c[0]) for c in CATEGORIES)
    return re.sub(rf'(?<![\w-])category-({shelves})\.html', rf'category-\1{DEMO_SUFFIX}.html', page)


def demo_report(pages, style):
    """What the demo links that main does not have yet: those files have to ship with it."""
    import subprocess
    # our own files only: relative paths, and BASE-prefixed ones (og:image); not another host's assets/
    text = ''.join(pages.values()) + style
    refs = set(re.findall(r'(?<![\w./-])assets/[A-Za-z0-9_./-]+\.[a-z0-9]{2,5}', text.replace(BASE, '')))
    refs |= {'site.webmanifest'} if 'site.webmanifest' in text else set()
    try:
        have = set(subprocess.run(['git', 'ls-tree', '-r', 'main', '--name-only'], cwd=ROOT, check=True,
                                  capture_output=True, text=True).stdout.split())
    except (OSError, subprocess.CalledProcessError) as e:
        raise SystemExit(f'--demo: could not list main ({e})')
    new = sorted(r for r in refs if r not in have)
    missing = [r for r in new if not os.path.exists(os.path.join(ROOT, r))]
    print(f'demo: {len(pages)} pages in {DEMO} + {DEMO_STYLE} ({len(refs)} asset references)')
    for n in pages:
        print('  ' + n)
    print(f'assets the demo references that main does not have: {len(new)}')
    for r in new:
        print('  ' + r + ('   (MISSING here too)' if r in missing else ''))
    if missing:
        raise SystemExit('--demo: some referenced files do not exist; run a normal build first')


if __name__ == '__main__':
    def arg(flag):
        i = sys.argv.index(flag)
        if i + 1 >= len(sys.argv):
            raise SystemExit('usage: build_homepage.py [--ccrx on|off] [--no-plus]\n'
                             '                         [--demo OUTDIR [--demo-name NAME]] [--view bar|case|strip|ring]')
        return sys.argv[i + 1]
    if '--view' in sys.argv:
        SHELF_VIEW = arg('--view')
        if SHELF_VIEW not in ('bar', 'case', 'strip', 'ring'):
            raise SystemExit(f'--view: no such view {SHELF_VIEW!r}')
    if '--demo-name' in sys.argv:
        if '--demo' not in sys.argv:
            raise SystemExit('--demo-name goes with --demo OUTDIR')
        name = arg('--demo-name')
        if not re.fullmatch(r'[a-z0-9-]+', name):
            raise SystemExit('--demo-name: lower-case letters, digits and hyphens only')
        DEMO_SUFFIX = f'-demo-{name}'
        DEMO_PAGE, DEMO_STYLE = f'homepage{DEMO_SUFFIX}.html', f'style-demo-{name}.css'
    if '--ccrx' in sys.argv:  # the switch, forced for this run; the second pass sets it on regardless
        v = arg('--ccrx')
        if v not in ('on', 'off'):
            raise SystemExit("--ccrx: on or off")
        CCRX = v == 'on'
    if '--no-plus' in sys.argv:  # plain site only, e.g. while working on something else
        PLUS_BUILD = False
    if '--demo' in sys.argv:
        DEMO = os.path.abspath(arg('--demo'))  # the repo root is fine: the export only adds its own files
        os.makedirs(DEMO, exist_ok=True)
    main()
    if PLUS_BUILD and not DEMO:
        # the second pass: the same source, the same products, the same photos, written into
        # PLUS_DIR/ with the switch on. It is the only copy allowed to carry the CCRX link.
        PLUS, CCRX = True, True
        main()
