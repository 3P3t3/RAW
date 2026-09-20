"""Build homepage.html from share-links.csv + product-photos/.

Run from the project folder:  python3 site-src/build_homepage.py
Edit share-links.csv (product, share_link, photo) and re-run to update the site.
"""
import csv, html, json, os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'site-src', 'homepage.template.html')
OUT = os.path.join(ROOT, 'homepage.html')
PHOTOS = os.path.join(ROOT, 'product-photos')
STUDIO = os.path.join(ROOT, 'product-shots')  # re-lit studio versions, already framed to one scale
ASSETS = os.path.join(ROOT, 'assets', 'products')

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


def main():
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

    counts = {g: sum(g in p['goals'] for p in products) for g in 'RLES'}
    goals = []
    for i, (g, name, line, prod) in enumerate(GOAL_TILES):
        img = by[prod]['img']
        hi = ' fetchpriority="high"' if i < 2 else ''
        goals.append(
            f'          <li><a class="goal" href="#shop" data-goal="{g}">'
            f'<span class="goal-name">{name}</span><span class="goal-desc">{line}</span>'
            f'<span class="goal-n">{counts[g]} products</span>'
            f'<span class="goal-img"><img src="{img}" alt="" width="600" height="600" loading="lazy"></span></a></li>')

    order = [by[n] for n in FEATURED] + sorted((p for p in products if p['product'] not in FEATURED), key=lambda p: p['product'].lower())
    grid = []
    for p in order:
        extra = '' if p['product'] in FEATURED else ' data-extra hidden'
        u = esc(p['share_link'])
        grid.append(
            f'        <li class="card" data-goals="{p["goals"]}"{extra}>'
            f'<a class="card-link" href="{u}" target="_blank" rel="noopener">{shot(p)}'
            f'<p class="p-tag">{GOAL_NAMES.get(p["goals"][:1], "Wellness")}</p><h3 class="p-name">{esc(p["name"])}</h3>'
            f'<p class="p-desc">{esc(p["desc"])}</p><span class="vh">Buy on Amway (opens in a new tab)</span></a></li>')

    index = [f'        <li><a href="{esc(p["share_link"])}" target="_blank" rel="noopener">{esc(p["product"].replace("n- by", "n* by"))}</a></li>'
             for p in sorted(products, key=lambda p: p['product'].lower().lstrip('n*- '))]

    finder = {}
    for key, name, why in FINDER:
        p = by[name]
        finder[key] = dict(name=p['name'], desc=p['desc'], img=p['img'], url=p['share_link'], g=p['goals'], form=p['form'], why=why)

    duo = [by['XS Grass-Fed Whey Protein - Chocolate'], by['XS Creatine+']]
    out = open(SRC).read()
    subs = {
        '{{GOALS}}': '\n'.join(goals),
        '{{GRID}}': '\n'.join(grid),
        '{{INDEX}}': '\n'.join(index),
        '{{TOTAL}}': str(len(products)),
        '{{FINDER_DATA}}': json.dumps(finder, ensure_ascii=False).replace('</', '<\\/'),
        '{{DUO_IMGS}}': ''.join(f'<img src="{p["img"]}" alt="" loading="lazy" width="600" height="600">' for p in duo),
        '{{DUO_ALT}}': 'XS Grass-Fed Whey Protein and XS Creatine+, a typical finder result',
        '{{TRUST_IMG}}': by['XS Juiced and Burn 12 oz - Variety Case']['img'],
        '{{TRUST_ALT}}': 'XS Juiced and Burn energy drink variety case',
        '{{LABEL_URL}}': esc(by['XS Grass-Fed Whey Protein - Chocolate']['share_link']),
    }
    for k, v in subs.items():
        out = out.replace(k, v)
    open(OUT, 'w').write(out)
    print(f'{len(products)} products ({sum(1 for p in products if p["img"])} with photos) -> {OUT}')
    print('goal counts', counts)


if __name__ == '__main__':
    main()
