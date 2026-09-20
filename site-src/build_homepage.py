"""Build homepage.html from share-links.csv + product-photos/.

Run from the project folder:  python3 site-src/build_homepage.py
Edit share-links.csv (product, share_link, photo) and re-run to update the site.
"""
import csv, hashlib, html, inspect, json, os, re, shutil

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
CATEGORIES = [
    ('recovery', 'Recovery', 'Wind down, repair and sleep: post-workout mixes, magnesium, herbals and topical creams.', 'Everything in Recovery', [
        'XS Post-Workout Recovery', 'XS Muscle Multiplier', 'XS CBD Cream', 'XS CBD Pro Cream',
        'Nutrilite Magnesium', 'Nutrilite Organics Ashwagandha Capsules', 'Nutrilite Organics Chamomile Tea',
        'Nutrilite Sleep Health', 'n* by Nutrilite Sweet Dreams']),
    ('hydration', 'Hydration', 'Electrolytes and drink mixes for long, hot and sweaty sessions.', 'Everything in Hydration', [
        'XS Sports Twist Tubes', 'Nutrilite Twist Tubes 2GO', 'XS CocoWater Hydration Drink Mix']),
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

# The flavour carousel: category slug -> (family prefix to pull, heading, line)
CAROUSELS = {
    'energy-focus': ('XS Energy Drink 12 oz', 'Pick your flavour', 'The 12 oz range, one can at a time.'),
}

SHELF_LINE = {  # the line under each shelf name in the ring
    'recovery': 'After the session', 'hydration': 'Electrolytes', 'energy-focus': 'Cans & capsules',
    'protein': 'Whey, bars, crisps', 'fat-loss': 'Thermogenic', 'daily-foundations': 'Everyday basics',
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

# Calendly (or any booking) link for the consult section. The four answers ride along as a1-a4;
# leave it empty and the form says the calendar is not connected yet instead of opening a dead page.
CONSULT_URL = ''

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

GOAL_TILES = [  # goal, name, line, product shown in the goal index (none of these repeat in the picks)
    ('R', 'Recovery', 'Bounce back between sessions', 'XS Post-Workout Recovery - Fruit Punch (12 Stick Packs)'),
    ('L', 'Lean Mass', 'Build muscle and keep it', 'XS Sports Protein Bars - Chocolate Peanut Butter'),
    ('E', 'Endurance', 'Energy and hydration that lasts', 'XS Sports Twist Tubes - Raspberry Lemonade'),
    ('S', 'Sleep &amp; Longevity', 'Rest deeper, age well', 'Nutrilite Sleep Health'),
]

# Finder candidates: one per product family, each with a plain-language reason (no health claims).
FINDER = [
    ('whey', 'XS Grass-Fed Whey Protein - Chocolate', 'Grass-fed whey protein to help you hit your daily protein, shaken up after training.'),
    ('creatine', 'XS Creatine+', 'Creatine in one simple daily scoop, a staple for strength and power work.'),
    ('recovery', 'XS Post-Workout Recovery - Fruit Punch (30 Serving Pouch)', 'Made for right after training, when you want to refuel in one drink.'),
    ('multiplier', 'XS Muscle Multiplier - Berry Blast', 'A flavored mix to sip during or after lifting sessions.'),
    ('preworkout', 'XS Pre-Workout Boost - Blue Raspberry (30 Serving Pouch)', 'Mixed before a session when you want more drive in your workout.'),
    ('coco', 'XS CocoWater Hydration Drink Mix - Pineapple/Coconut', 'A hydration mix for long, sweaty sessions and hot days.'),
    ('energy', 'XS Energy Drink 12 oz - Variety Case', 'Zero-sugar energy drinks, cold and ready when you need a lift before training.'),
    ('tablets', 'XS Energy + Focus Dietary Supplement - 30 Tablets', 'Energy in tablet form, for when you would rather skip the can.'),
    ('tubes', 'XS Sports Twist Tubes - Raspberry Lemonade', 'Pocket-size tubes you twist into a water bottle on the go.'),
    ('shake', 'XS Sports Protein Shakes - Rich Chocolate', 'Ready-to-drink protein for after training, no shaker needed.'),
    ('bar', 'XS Sports Protein Bars - Chocolate Peanut Butter', 'A protein bar that can live in your gym bag.'),
    ('crisps', 'XS Protein Crisps - Sriracha Lime', 'A savory, crunchy protein snack between meals.'),
    ('cbd', 'XS CBD Cream', 'A CBD cream to massage into the spots that feel worked after training.'),
    ('sleep', 'Nutrilite Sleep Health', 'A nightly supplement from Nutrilite to build into your wind-down routine.'),
    ('gummies', 'n* by Nutrilite Sweet Dreams - Sleep Gummies', 'A bedtime gummy for the last step of your evening routine.'),
    ('tea', 'Nutrilite Organics Chamomile Tea', 'Organic chamomile tea, a caffeine-free way to close out the day.'),
    ('probiotic', 'Nutrilite Balance Within Probiotic', 'A daily probiotic for the long-game side of your health.'),
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


def esc(s):
    return html.escape(s, quote=True)


def shot(p, lazy=True, cls='shot'):
    if p.get('studio'):
        cls += ' shot-studio'
    if p['img']:
        ld = 'loading="lazy" ' if lazy else ''
        return f'<span class="{cls}"><img src="{p["img"]}" alt="" {ld}width="600" height="600"></span>'
    return f'<span class="ph" aria-hidden="true"><span class="ph-cap"><b>Photo</b><br>coming soon</span></span>'


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
            shutil.copyfile(studio, os.path.join(ASSETS, fn))
            p['img'] = 'assets/products/' + fn
            p['studio'] = True
            products.append(p)
            continue
        if src and os.path.exists(src):
            fn = slug(r['product']) + os.path.splitext(src)[1].lower()
            normalize(src, os.path.join(ASSETS, fn))
            p['img'] = 'assets/products/' + fn
        else:
            p['img'] = ''
        products.append(p)
    by = {p['product']: p for p in products}
    for n in FEATURED + [t[3] for t in GOAL_TILES] + [f[1] for f in FINDER]:
        assert n in by, f'Missing product in CSV: {n}'

    cat_of = {}
    for slug_, name, tag, heading, fams in CATEGORIES:
        for pr in products:
            if family(pr['product']) in fams:
                cat_of[pr['product']] = slug_
    counts = {c[0]: sum(1 for pr in products if cat_of.get(pr['product']) == c[0]) for c in CATEGORIES}
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
                f'<span class="goal-island"><img src="assets/islands/{slug_}.webp" alt="" width="760" height="760" loading="lazy"></span></a></li>')
        return '\n'.join(out_)

    isles = []
    for i, (slug_, name, tag, heading, fams) in enumerate(CATEGORIES):
        prio = ' fetchpriority="high"' if i < 3 else ' loading="lazy"'
        line = SHELF_LINE[slug_]
        isles.append(
            f'        <li class="isle" style="--i:{i}"><a href="category-{slug_}.html">'
            f'<span class="isle-art"><img src="assets/islands/{slug_}.webp" alt="" width="760" height="760"{prio}></span>'
            f'<span class="isle-label"><span class="isle-name">{name}</span>'
            f'<span class="isle-note">{line}</span></span></a></li>')

    order = sorted(products, key=lambda pr: pr['name'].lower())
    grid = [card(pr, i) for i, pr in enumerate(order)]

    finder = {}
    for key, name, why in FINDER:
        pr = by[name]
        finder[key] = dict(name=pr['name'], desc=pr['desc'], img=pr['img'], url=pr['share_link'], g=pr['goals'], form=pr['form'], why=why)
    finder_json = json.dumps(finder, ensure_ascii=False).replace('</', '<\\/')

    part = lambda n: open(os.path.join(ROOT, 'site-src', n)).read()
    style, header, footer, dialogs, script, icons = (part('style.css'), part('_header.html'), part('_footer.html'),
                                                     part('_dialogs.html'), part('_script.html'), part('_icons.html'))
    open(STYLE_OUT, 'w').write(style)  # served once and cached, instead of inlined into all eight pages
    style_href = 'style.css?v=' + hashlib.sha1(style.encode()).hexdigest()[:8]  # bust the cache when the css moves
    shared = {'{{STYLE}}': style_href, '{{FOOTER}}': footer, '{{DIALOGS}}': dialogs, '{{SCRIPT}}': script,
              '{{ICONS}}': icons, '{{TOTAL}}': str(len(products)), '{{CONSULT_URL}}': CONSULT_URL,
              '{{FINDER_DATA}}': finder_json}

    os.makedirs(CUTS, exist_ok=True)
    podium = []
    for i, r in enumerate(bestsellers()[:3]):
        pr = dict(by.get(r['product']) or {})
        if not pr:
            raise SystemExit(f"bestsellers.csv: no such product {r['product']!r}")
        photo = next((row['photo'] for row in rows if row['product'] == r['product']), '')
        if photo and os.path.exists(os.path.join(PHOTOS, photo)):  # transparent cut-out for the dark band
            fn = slug(r['product']) + '.webp'
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

    out = open(SRC).read()
    for k, v in dict(shared, **{'{{HEADER}}': header.replace('{{HOME}}', ''), '{{HOME}}': '',
                                '{{GOALS}}': cat_rows(), '{{GRID}}': '\n'.join(grid), '{{PODIUM}}': '\n'.join(podium), '{{ISLANDS}}': '\n'.join(isles)}).items():
        out = out.replace(k, v)
    open(OUT, 'w').write(out)

    cat_tpl = open(os.path.join(ROOT, 'site-src', 'category.template.html')).read()
    for slug_, name, tag, heading, fams in CATEGORIES:
        items = [pr for pr in products if cat_of.get(pr['product']) == slug_]
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
            carousel = f'''  <!-- Flavour carousel: glides on its own, arrows or swipe to take over -->
  <section class="sec carousel-sec" aria-labelledby="flavours-title">
    <div class="wrap">
      <div class="sec-head grow"><h2 id="flavours-title">{chead}</h2>
        <div class="car-nav"><button class="icon-btn" type="button" data-car="-1" aria-label="Previous flavour"><svg class="ic" aria-hidden="true"><use href="#i-back"/></svg></button><button class="icon-btn" type="button" data-car="1" aria-label="Next flavour"><svg class="ic" aria-hidden="true"><use href="#i-arrow"/></svg></button></div>
      </div>
      <p class="sec-note">{cline}</p>
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
                '{{CAT_NAME}}': name, '{{CAT_TAG}}': tag, '{{CAT_HEADING}}': heading,
                '{{CAT_COUNT}}': str(counts[slug_]), '{{CAT_GRID}}': cgrid, '{{CAROUSEL}}': carousel,
                '{{CAT_OTHERS}}': cat_rows(only={slug_}), '{{CAT_BG}}': f'assets/bg-{slug_}.webp'}).items():
            page = page.replace(k, v)
        open(os.path.join(ROOT, f'category-{slug_}.html'), 'w').write(page)

    open(STAMP, 'w').write(cut_version())  # last, so a crash leaves the old stamp and the next run re-cuts
    print(f'{len(products)} products ({sum(1 for pr in products if pr["img"])} with photos) -> {OUT}')
    print('categories', counts, 'uncategorised', [pr['product'] for pr in products if pr['product'] not in cat_of])


if __name__ == '__main__':
    main()
