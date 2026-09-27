"""Build homepage.html from share-links.csv + product-photos/.

Run from the project folder:  python3 site-src/build_homepage.py
Edit share-links.csv (product, share_link, photo) and re-run to update the site.
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
# `--demo OUTDIR` exports a public copy of the homepage and writes nothing else: OUTDIR/homepage-demo.html,
# linked to its own OUTDIR/style-demo.css, so the live pages and their shared style.css are never touched.
# It is noindexed, and its canonical and og:url name the demo's own address. It photographs nothing
# (no cut-outs, no copies), so run a normal build first; it then lists what it links that main lacks.
DEMO = None
DEMO_PAGE = 'homepage-demo.html'
DEMO_STYLE = 'style-demo.css'

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
}

# Category pages: slug, name, tagline, heading, family prefixes that belong to it.
# A family may sit on more than one shelf: each shelf page lists everything its own list names.
# Its card tag (and its data-cat) names one home shelf, the later of them in this list.
CATEGORIES = [
    ('recovery', 'Recovery', 'Wind down, repair and sleep: post-workout mixes, magnesium, herbals and topical creams.', 'Everything in Recovery', [
        'XS Post-Workout Recovery', 'XS Muscle Multiplier', 'XS CBD Cream', 'XS CBD Pro Cream',
        'Nutrilite Magnesium', 'Nutrilite Organics Ashwagandha Capsules', 'Nutrilite Organics Chamomile Tea',
        'Nutrilite Sleep Health', 'n* by Nutrilite Sweet Dreams']),
    ('hydration', 'Hydration', 'Electrolytes and drink mixes for long, hot and sweaty sessions.', 'Everything in Hydration', [
        'XS Sports Twist Tubes', 'Nutrilite Twist Tubes 2GO', 'XS CocoWater Hydration Drink Mix',
        'XS Creatine+']),  # also on Daily Foundations: it is half of Peter's hydration stack
    ('energy-focus', 'Energy &amp; Focus', 'Pre-workout, tablets and the full XS energy range.', 'Everything in Energy &amp; Focus', [
        'XS Pre-Workout Boost', 'XS Energy + Focus Dietary Supplement', 'XS Energy Drink 12 oz',
        'XS Energy + Burn 12 oz', 'XS Juiced and Burn 12 oz', 'XS Sparkling Juiced Energy 12 oz',
        'XS Elite + Focus Energy Drink']),
    ('protein', 'Protein Snack Pack', 'Powders, shakes, bars and crisps to hit your protein for the day.', 'Everything in Protein', [
        'XS Grass-Fed Whey Protein', 'XS Grass-Fed Whey Protein Powder Sachets', 'XS Sports Protein Bars',
        'XS Sports Protein Shakes', 'XS Protein Crisps', 'Nutrilite Organics All-in-One Bars']),
    ('fat-loss', 'Fat Loss', 'Thermogenic support to pair with your training.', 'Everything in Fat Loss', [
        'XS Ignite Powder']),
    ('daily-foundations', 'Daily Foundations', 'The everyday base: creatine, gut health and digestion.', 'Everything in Daily Foundations', [
        'XS Creatine+', 'Nutrilite Begin Daily GI Primer', 'Nutrilite Balance Within Probiotic']),
    ('skin-redefined', 'Skin Redefined', 'Artistry skincare, for the hours you are not training.', 'Everything in Skin Redefined', [
        'Artistry Skin Nutrition Renewing Softening Toner', 'Artistry Skin Nutrition Sleeping Mask',
        'Artistry Studio Glow Boss Cleanser + Exfoliator']),
]

# The flavor carousel: category slug -> (family prefix to pull, heading, line)
CAROUSELS = {
    'energy-focus': ('XS Energy Drink 12 oz', 'Pick your flavor', 'The 12 oz range, one can at a time.'),
}

# 'case' is the stack case: the seven shelves as the seven compartments of one case, each lid a
# button that opens onto a few of that shelf's packs. 'strip' is the tabbed goal strip; 'ring'
# brings back the rotating archipelago. All three are built from the same shelf data, so switching
# is this one word plus a rebuild; the ring's script and styles stay in, idle while it is off.
SHELF_VIEW = 'case'
CASE_PICKS = 3  # packs an open compartment shows: one per family, in the shelf's own order

# The trending band's ground: True scrubs the 150-frame pour behind the podium, False leaves the
# band plain teal and fetches none of it. The frames and the script stay either way.
TRENDING_POUR = False

SHELF_LINE = {  # the line under each shelf name
    'recovery': 'After the session', 'hydration': 'Long, hot sessions', 'energy-focus': 'Before the session',
    'protein': 'Hitting your protein', 'fat-loss': 'Training to lean out', 'daily-foundations': 'Everyday basics',
    'skin-redefined': 'Skin & overnight',
}

CAT_THUMB = {  # the pack shown on the homepage row for each category
    'recovery': 'XS Post-Workout Recovery - Fruit Punch (12 Stick Packs)',
    'hydration': 'XS Sports Twist Tubes - Raspberry Lemonade',
    'energy-focus': 'XS Energy Drink 12 oz - Classic',
    'protein': 'XS Sports Protein Bars - Chocolate Peanut Butter',
    'fat-loss': 'XS Ignite Powder - Moro Blood Orange',
    'daily-foundations': 'XS Creatine+',
    'skin-redefined': 'Artistry Skin Nutrition Sleeping Mask',
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
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'share-links.csv'), newline='')))
    os.makedirs(ASSETS, exist_ok=True)
    products = []
    for r in rows:
        p = describe(r)
        src = os.path.join(PHOTOS, r['photo']) if r['photo'] else ''
        studio = os.path.join(STUDIO, slug(r['product']) + '.webp')
        if os.path.exists(studio):
            fn = slug(r['product']) + '.webp'
            if not DEMO:
                shutil.copyfile(studio, os.path.join(ASSETS, fn))
            p['img'] = 'assets/products/' + fn
            p['studio'] = True
            products.append(p)
            continue
        if src and os.path.exists(src):
            fn = slug(r['product']) + os.path.splitext(src)[1].lower()
            if not DEMO:
                normalize(src, os.path.join(ASSETS, fn))
            p['img'] = 'assets/products/' + fn
        else:
            p['img'] = ''
        products.append(p)
    by = {p['product']: p for p in products}
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

    def card(pr, i=0, extra=''):
        u = esc(pr['share_link'])
        tag = names.get(cat_of.get(pr['product']), 'Wellness')
        return (f'        <li class="card grow" style="--d:{i % 4}" data-cat="{cat_of.get(pr["product"], "")}"{extra}>'
                f'<a class="card-link" href="{u}" target="_blank" rel="noopener">{shot(pr)}'
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

    def case_section():
        bays = []
        for i, (slug_, name, tag, heading, fams) in enumerate(CATEGORIES):
            packs = case_picks(slug_, fams)
            names_ = [pr['name'] for pr in packs]
            cells = '\n'.join(
                f'                <li class="bay-pack" style="--k:{j}"><img src="{pr["img"]}" alt="" width="600" height="600" '
                f'loading="lazy" decoding="async"><span>{esc(pr["name"] if names_.count(pr["name"]) == 1 else pr["desc"].split(" · ")[-1])}</span></li>'
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
                '\n        </ul>\n      </div>\n    </div>\n  </section>')

    shelves = {'ring': ring_section, 'strip': strip_section, 'case': case_section}[SHELF_VIEW]()
    # the story's stack is the same case in miniature: the same seven compartments, in the same order,
    # empty until the story's packs tuck into them (_script.html measures them; nothing here moves)
    case_strip = ('<div class="st-row st-case" aria-hidden="true"><span class="stc-body">'
                  + ''.join(f'<span class="stc-bay" data-cat="{s}"><span class="stc-well"></span>'
                            f'<span class="stc-name">{n}</span></span>' for s, n, *_ in CATEGORIES)
                  + '</span></div>')
    pour = ('''<div class="pour-bg" id="pour-bg" aria-hidden="true">
      <div class="pour-stage">
        <canvas class="pour-film" id="pour-film"></canvas>
        <img class="pour-still" id="pour-still" alt="" decoding="async" hidden>
        <noscript><img class="pour-still" src="assets/pour/sm/0060.webp" alt=""></noscript>
      </div>
    </div>''' if TRENDING_POUR else '<!-- TRENDING_POUR is off in build_homepage.py: a plain band -->')

    order = sorted(products, key=lambda pr: pr['name'].lower())
    grid = [card(pr, i) for i, pr in enumerate(order)]

    part = lambda n: open(os.path.join(ROOT, 'site-src', n)).read()
    style, header, footer, dialogs, script, icons = (part('style.css'), part('_header.html'), part('_footer.html'),
                                                     part('_dialogs.html'), part('_script.html'), part('_icons.html'))
    intro = part('_intro.html')  # the opening curtain: homepage only, so it is not in `shared`
    style_file = os.path.join(DEMO, DEMO_STYLE) if DEMO else STYLE_OUT
    open(style_file, 'w').write(style)  # served once and cached, instead of inlined into all eight pages
    style_href = os.path.basename(style_file) + '?v=' + hashlib.sha1(style.encode()).hexdigest()[:8]  # bust the cache when the css moves
    # the menu sheet lists every shelf; it follows {{DIALOGS}} in this dict so it fills the menu once it is in
    menu_shelves = '\n'.join(f'        <li><a href="category-{s}.html">{n}</a></li>' for s, n, *_ in CATEGORIES)
    shared = {'{{STYLE}}': style_href, '{{FOOTER}}': footer, '{{DIALOGS}}': dialogs, '{{MENU_SHELVES}}': menu_shelves,
              '{{SCRIPT}}': script,
              '{{ICONS}}': icons, '{{TOTAL}}': str(len(products)),
              '{{TOTAL_PRODUCTS}}': plural(len(products), 'product', zero='products'), '{{CONSULT_URL}}': CONSULT_URL,
              '{{BASE}}': BASE}
    # what the sample form's "What would you like to try?" suggests: every family, by the name its cards carry
    sample_list = '\n'.join(f'          <option value="{esc(n)}"></option>'
                            for n in sorted({pr['name'] for pr in products}, key=str.lower))

    if not DEMO:
        os.makedirs(CUTS, exist_ok=True)
    podium = []
    for i, r in enumerate(bestsellers()[:3]):
        pr = dict(by.get(r['product']) or {})
        if not pr:
            raise SystemExit(f"bestsellers.csv: no such product {r['product']!r}")
        photo = next((row['photo'] for row in rows if row['product'] == r['product']), '')
        if photo and os.path.exists(os.path.join(PHOTOS, photo)):  # transparent cut-out for the dark band
            fn = slug(r['product']) + '.webp'
            if not DEMO:
                normalize(os.path.join(PHOTOS, photo), os.path.join(CUTS, fn))
            pr['img'] = 'assets/cutouts/' + fn
            pr['studio'] = False
        units = (r.get('units_this_week') or '').strip()
        count = (f'<p class="pod-count"><span class="pod-num" data-count="{units}">0</span> '
                 f'bought this week</p>') if units.isdigit() else ''
        podium.append(
            f'        <li class="pod pod-{i + 1}"><a class="card-link tilt" href="{esc(pr["share_link"])}" target="_blank" rel="noopener">'
            f'<span class="pod-rank" aria-hidden="true">0{i + 1}</span>'
            f'{shot(pr, lazy=False)}<p class="p-tag">{names.get(cat_of.get(pr["product"]), "Wellness")}</p>'
            f'<h3 class="p-name">{esc(pr["name"])}</h3><p class="p-desc">{esc(pr["desc"])}</p>{count}'
            f'<span class="vh">Buy on Amway (opens in a new tab)</span></a></li>')

    page_name = DEMO_PAGE if DEMO else 'homepage.html'
    head_extra = (f'<meta name="robots" content="noindex">\n<link rel="canonical" href="{BASE}{DEMO_PAGE}">\n'
                  if DEMO else '')
    out = open(SRC).read()
    for k, v in dict(shared, **{'{{HEADER}}': header.replace('{{HOME}}', ''), '{{HOME}}': '',
                                '{{HEAD_EXTRA}}': head_extra,
                                '{{PAGE_URL}}': BASE + page_name, '{{INTRO}}': intro,
                                '{{GOALS}}': cat_rows(),
                                '{{SAMPLE_ENDPOINT}}': SAMPLE_ENDPOINT, '{{SAMPLE_ACTION}}': SAMPLE_ACTION,
                                '{{SAMPLE_NEXT}}': SAMPLE_NEXT.replace('homepage.html', page_name), '{{SAMPLE_PRODUCTS}}': sample_list, **quick_call(), '{{GRID}}': '\n'.join(grid), '{{PODIUM}}': '\n'.join(podium), '{{SHELVES}}': shelves,
                                '{{CASE_STRIP}}': case_strip, '{{POUR}}': pour,
                                '{{POUR_CLASS}}': '' if TRENDING_POUR else ' no-pour'}).items():
        out = out.replace(k, v)
    left = sorted(set(re.findall(r'\{\{[A-Z_]+\}\}', out)))
    if left:
        raise SystemExit(f'unfilled placeholders in the homepage: {left}')
    if DEMO:
        open(os.path.join(DEMO, DEMO_PAGE), 'w').write(out)
        demo_report(out, style)
        return
    open(OUT, 'w').write(out)

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
                f'          <li class="slide"><a class="card-link" href="{esc(pr["share_link"])}" target="_blank" rel="noopener">'
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
        for k, v in dict(shared, **{
                '{{HEADER}}': header.replace('{{HOME}}', 'homepage.html'), '{{HOME}}': 'homepage.html',
                '{{PAGE_URL}}': BASE + f'category-{slug_}.html',
                '{{SAMPLE_LINK}}': 'homepage.html?try=' + quote(html.unescape(name)) + '#sample',
                '{{CAT_NAME}}': name, '{{CAT_TAG}}': tag, '{{CAT_HEADING}}': heading,
                '{{CAT_COUNT}}': plural(counts[slug_], 'product', zero='No products yet'), '{{CAT_GRID}}': cgrid, '{{CAROUSEL}}': carousel,
                '{{CAT_OTHERS}}': cat_rows(only={slug_}), '{{CAT_BG}}': f'assets/bg-{slug_}.webp'}).items():
            page = page.replace(k, v)
        open(os.path.join(ROOT, f'category-{slug_}.html'), 'w').write(page)

    open(STAMP, 'w').write(cut_version())  # last, so a crash leaves the old stamp and the next run re-cuts
    print(f'{len(products)} products ({sum(1 for pr in products if pr["img"])} with photos) -> {OUT}')
    print('categories', counts, 'uncategorised', [pr['product'] for pr in products if pr['product'] not in cat_of])


def demo_report(page, style):
    """What the demo links that main does not have yet: those files have to ship with it."""
    import subprocess
    # our own files only: relative paths, and BASE-prefixed ones (og:image); not another host's assets/
    refs = set(re.findall(r'(?<![\w./-])assets/[A-Za-z0-9_./-]+\.[a-z0-9]{2,5}', (page + style).replace(BASE, '')))
    refs |= {'site.webmanifest'} if 'site.webmanifest' in page else set()
    try:
        have = set(subprocess.run(['git', 'ls-tree', '-r', 'main', '--name-only'], cwd=ROOT, check=True,
                                  capture_output=True, text=True).stdout.split())
    except (OSError, subprocess.CalledProcessError) as e:
        raise SystemExit(f'--demo: could not list main ({e})')
    new = sorted(r for r in refs if r not in have)
    missing = [r for r in new if not os.path.exists(os.path.join(ROOT, r))]
    print(f'demo: {os.path.join(DEMO, DEMO_PAGE)} + {DEMO_STYLE} ({len(refs)} asset references)')
    print(f'assets the demo references that main does not have: {len(new)}')
    for r in new:
        print('  ' + r + ('   (MISSING here too)' if r in missing else ''))
    if missing:
        raise SystemExit('--demo: some referenced files do not exist; run a normal build first')


if __name__ == '__main__':
    if '--demo' in sys.argv:
        i = sys.argv.index('--demo')
        if i + 1 >= len(sys.argv):
            raise SystemExit('usage: build_homepage.py --demo OUTDIR')
        DEMO = os.path.abspath(sys.argv[i + 1])  # the repo root is fine: the export only adds its own two files
        os.makedirs(DEMO, exist_ok=True)
    main()
