# The macro calculator

The homepage band at `#macros` asks seven questions and prints a day's calorie and macro
targets. All of its arithmetic lives in one function, `mcCalc(v)` in
`site-src/_script.html` (between the `mc:calc` and `mc:end` comment markers). This file is
the record of where that arithmetic came from and exactly what it does. It was written by
reading `mcCalc` and re-running it, not from memory.

`mcCalc` is defined in the script that every page ships, but the form it serves
(`#mc-form`) only exists on the homepage, so on the category pages the function is present
and never called.

## Where the maths came from

The formulas were reverse-engineered from a calculator belonging to a friend of Peter's,
published at <https://macro-calculator-xi.vercel.app/>, **with that friend's explicit
permission**. It is a single hand-written HTML file with one inline `<script>` and one
`calculate()` function — no bundler, no API. Imperial units only, and no body-fat input.

Aspire's version reproduces that maths deliberately and digit for digit, with five
departures that are listed below.

**This document is a record, not a licence.** It states what was done and that permission
was given. It does not grant anyone else any right to the source calculator's code or
design, and it is not a copyright or licensing assertion about either calculator. If the
provenance of this maths ever needs to be settled properly, it needs to be settled with
the owner, not with this file.

## The formulas, as implemented

Read out of `mcCalc` itself. Names below are the code's own.

### Inputs

| Input | Values | Where they come from |
|---|---|---|
| `sex` | `male`, `female` | radio, **no default** |
| `age` | whole years, **13 to 100** | number field |
| `weightLb` | pounds, **50 to 700** | number field |
| `ft`, `inch` | feet **3 to 8**, inches **0 to 11**; total height must land between 36 and 96 inches | two number fields; inches may be blank, feet in practice cannot, because inches alone can no longer reach three feet |
| `activity` | 1.2, 1.375, 1.55, 1.725 | radio, default **1.55** |
| `basis` | `standard`, `better`, `trained` | radio, default **standard** |
| `frame` | 0.95, 1, 1.15 (small / medium / large) | only used when `basis` is `better`, default 1 |
| `trained` | 1, 1.2 (g per lb) | only used when `basis` is `trained`, default 1 |
| `goal` | `loss`, `recomp`, `maint`, `gain` | radio, default **maint** |
| `loss` | 0.85, 0.8, 0.75 | only used when `goal` is `loss`, default 0.85 |

### 1. Unit conversion

    wKg = weightLb * 0.453592
    hIn = ft * 12 + inch
    hCm = hIn * 2.54

### 2. BMR — Mifflin–St Jeor, on total bodyweight

    bmr = 10*wKg + 6.25*hCm - 5*age + (sex === 'male' ? 5 : -161)

The `+5` / `-161` constant is the only place `sex` affects the calorie side. Total
bodyweight is used, not lean mass — there is no body-fat input to work from.

### 3. Maintenance

    tdee = bmr * activity

Activity multipliers, to the exact decimal the form submits:

| Answer | Multiplier |
|---|---|
| Sedentary — desk job, little exercise | **1.2** |
| Light — exercise 1–3× a week | **1.375** |
| Moderate — exercise 3–5× a week | **1.55** |
| Very active — exercise 6–7× a week | **1.725** |

### 4. Target calories

    goal 'loss'   -> target = tdee * loss     (loss is 0.85, 0.8 or 0.75)
    goal 'recomp' -> target = tdee * 0.92
    goal 'gain'   -> target = tdee * 1.12
    goal 'maint'  -> target = tdee

Goal factors: fat loss 0.85 (moderate, 15% under), 0.8 (standard, 20% under) or 0.75
(aggressive, 25% under); recomp **0.92**; muscle gain **1.12**; maintain **1.00**.

Then Peter's floor, which the source does not have:

    if (target < 1100) { target = 1100; floored = true }

The comparison is against the unrounded target, so a target of 1,099.6 is floored even
though it would have displayed as 1,100.

The floor can land level with, or above, maintenance: a small, older, sedentary person can
have a TDEE under 1,100, and then every deficit setting floors to the same 1,100 and the
card would be showing a "target" above maintenance on a fat-loss goal. `noRoom` names that
state:

    noRoom = (goal === 'loss' || goal === 'recomp') && target >= tdee * 0.97

`target` here is the floored figure. The 0.97 catches the neighbouring case as well — a
"deficit" of under 3% of maintenance, which the floor can also produce (the widest such gap
is 34 calories) and which is not a deficit in any useful sense. Only the floor can set
`noRoom`: the goal factors are 0.85 at their gentlest and 0.92 for recomp, both below 0.97,
so an unfloored target can never reach it. **`noRoom` changes no number.** It only changes
what the page says; see departure 5.

### 5. Ideal bodyweight — Devine, clamped at 5'0"

    over  = Math.max(hIn - 60, 0)
    ibwLb = ((sex === 'male' ? 50 : 45.5) + 2.3 * over) * 2.20462

Devine gives ideal bodyweight in kilograms: 50 kg for a man, 45.5 kg for a woman, plus
2.3 kg per inch over five feet. The `Math.max(..., 0)` is the clamp: **below 5'0" the
formula stops moving.** Everyone under five feet is treated as exactly five feet, because
Devine is undefined below that and subtracting would run the number down toward nothing.

### 6. Protein — three bases

    standard: proteinG = Math.round(ibwLb)
    better:   proteinG = Math.round(ibwLb * frame * 1.15)
    trained:  proteinG = Math.round(weightLb * trained)

| Basis | Form wording | Formula | Note |
|---|---|---|---|
| `standard` | New to this | 1 g per lb of **ideal** bodyweight | height-derived only; weight is not used |
| `better` | Training regularly | ideal bodyweight × frame (0.95 / 1 / 1.15) × **1.15** | the 1.15 is a flat uplift, applied on top of the frame factor |
| `trained` | Years in | **actual** bodyweight × 1 or 1.2 g per lb | the only basis that uses what you actually weigh |

### 7. Fat — a flat 30% share

    fatCal = Math.round(target * 0.30)
    fatG   = Math.round(fatCal / 9)

Fat is always 30% of the target calories, whatever the goal.

### 8. Carbohydrate — the remainder

    proteinCal = proteinG * 4          /* the rounded grams, not the raw value */
    spare      = target - proteinCal - fatCal
    carbCal    = Math.max(spare, 0)
    carbG      = Math.round(carbCal / 4)

Carbohydrate is not calculated. It is whatever the target has left after protein and fat
have taken their share, and it is floored at zero. When `spare` is negative the function
returns `clamped: true` and the page prints a warning; the numbers themselves are left
exactly as calculated (see departures, below).

### The two oddities the code comments flag

**The conversion constants are not reciprocals.** Pounds go to kilograms with `0.453592`;
kilograms come back to pounds with `2.20462`, marked in the code `do not tidy`. The true
reciprocal of 0.453592 is 2.2046244…, so `2.20462` is low by about 4.4 parts per million.
The source calculator has exactly this pair, and matching it digit for digit is the whole
point of the implementation.

Honesty about the size of this: a sweep of every whole-inch height from 4'0" to 7'0",
both sexes, all three frame settings, on both the `standard` and `better` bases, found
**no case where swapping in the reciprocal changes the displayed gram**. The rounding
absorbs a 4-ppm difference at these multipliers. So the code comment's implication —
that tidying this would move people's numbers — could not be reproduced as of the date
below. What remains true is that tidying it buys nothing, breaks the digit-for-digit
match with the source, and puts a difference back in play the moment a protein
multiplier changes or a new basis is added. Leave it alone.

**Fat is rounded twice.** `fatCal` is rounded to whole calories, then `fatG` is computed
from that rounded figure rather than from `target * 0.30`. Same honesty here: a sweep of
3.4 million targets from 1,100 to 4,500 in 0.001-calorie steps found no case where the
double rounding produces a different fat gram from a single rounding, and the arithmetic
explains why — `fatCal` is always a whole number, while the half-gram boundaries sit at
9k+4.5 calories, so rounding `fatCal` can never carry it across one.

What the double rounding *does* change is carbohydrate. The rounded `fatCal` is what gets
subtracted in `spare`, so carbs are computed against whole-calorie fat, not raw fat. That
is a real, if sub-gram, difference, and it is also what the source does. The rule for both
oddities is the same: the order of operations is the specification. Reordering the
roundings, or replacing a constant, means the implementation is no longer a copy of what
was verified, and every number on the page becomes unverified again.

## Rounding, in order

Nothing is rounded until step 4. In order:

1. `wKg`, `hIn`, `hCm`, `bmr`, `tdee`, `target`, `ibwLb` — **all unrounded**, full float.
2. The 1,100 floor is compared against the **unrounded** `target`.
3. `proteinG` — rounded. This is the first rounding whose result feeds later arithmetic.
4. `fatCal = Math.round(target * 0.30)` — rounded from the unrounded target.
5. `fatG = Math.round(fatCal / 9)` — rounded from the **already rounded** `fatCal`.
6. `proteinCal = proteinG * 4` — from the rounded grams, so it is exact by construction.
7. `spare = target - proteinCal - fatCal` — unrounded target minus two rounded calorie figures.
8. `carbG = Math.round(carbCal / 4)`, `carbCal` rounded for display.
9. `tdee` and `target` rounded last, for display only.

Because the displayed calorie figures are rounded independently, the three macro calorie
columns are not guaranteed to sum to the displayed target. In practice they usually do
(all nine examples below do); a one-calorie discrepancy is possible and is not a bug.

## Peter's deliberate departures from the source

| # | Departure | Reason |
|---|---|---|
| 1 | **A 1,100-calorie floor.** `if (target < 1100) { target = 1100; floored = true }`, and the page says so: "Floor reached. We don't go below 1,100 calories — a gentler deficit is the better way down." That note is suppressed when `noRoom` is set, because at that point a gentler deficit is not a way down either (departure 5). | The source has no floor at all. A small, older person on an aggressive deficit can be handed a number in the 700s with nothing said about it. Verified: profile 6 below gets 806 calories from the source. |
| 2 | **A warning when protein and fat alone exceed the target**, instead of a quiet adjustment. `clamped` is set when `spare < 0`, and the page prints: "Hold it — the math isn't mathing. Your protein and fat already use X of your Y calories, leaving nothing for carbs. This isn't sustainable. Ease the deficit or the protein setting and try again." **The numbers stand exactly as calculated** — carbs show 0 g, and nothing is silently reduced to make the arithmetic close. | Adjusting the inputs behind someone's back would hide the fact that their answers do not add up. The source shows `0g` carbs and says nothing. |
| 3 | **No body-fat input.** | The source has none either, so protein is derived from ideal bodyweight rather than measured lean mass. This is a departure from what a fuller calculator would do, not from the source; it is recorded here so nobody adds a body-fat field assuming the maths can use it. It cannot — nothing in `mcCalc` takes one. |
| 4 | **Sex is not pre-selected.** Neither radio carries `checked`, and step 1 will not advance without an answer: "Pick one so the formula knows which constant to use." | The source defaults to Female (`let sex = 'female'`, and the Female button ships with `class="active"`). Someone who skims past that question gets a silently wrong BMR constant — 166 calories before the activity multiplier, more after it. Every other question keeps the source's own default (activity 1.55, basis standard, frame medium, 1 g/lb, goal maintain, 15% deficit). |
| 5 | **`noRoom`: a deficit goal the floor has flattened is not presented as a deficit.** When the flag is set the card prints one warning — "This one doesn't look right — worth talking it through with one of our experts." — with *one of our experts* as a link into the consult, carrying the same goal and macro line the "Take these to a free call" button carries. The floor note and the goal note are both dropped in this state: the floor note recommends a gentler deficit and the fat-loss goal note says to "take another 5 to 10% off", and with the target already at or above maintenance both are advice against the arithmetic on the same card. Numbers, again, are not touched. | Before this, a 70-year-old woman at 95 lb and 4'10", sedentary, was shown "Maintenance 1,009 cal" and "Your target 1,100 cal" on a fat-loss goal, then told to cut a further 5 to 10%. The calculator cannot serve that person, and the honest move is to say so and hand her to a conversation rather than to a number. |
| 6 | **`offScale`: above 350 lb the card hands over instead of coaching.** `offScale: v.weightLb > 350`, strictly greater than, whatever the goal. It raises the same single warning as departure 5, with the same link and the same prefill, and it drops the floor note and the goal note for the same reason. | Peter's rule. Mifflin–St Jeor on total bodyweight has no upper guardrail, so before this a 78-year-old man at 400 lb and 4'11", very active, on a muscle-gain goal was shown 4,571 calories and 400 g of protein a day with nothing said. Those inputs pass every bound the form enforces (age 13–100, weight 50–700 lb, height 36–96 in), so no validation catches them. |
| 7 | **`overProtein`: a protein figure past 250 g hands over too.** `overProtein: proteinG > 250`, strictly greater than, on the rounded grams. Same single warning, same link. | The weight rule alone does not cover it: the ideal-bodyweight bases can hand a 350 lb visitor well under 250 g, while the 1.2 g/lb trained basis crosses 250 g at 209 lb and the 1 g/lb basis at 251 lb. **Peter considered capping protein at 250 g and chose not to** — a cap would make the card print a number the formula did not produce, which is the one thing this document exists to prevent. The figure stands as calculated and the card says it does not look right. |

All three handover states (`noRoom`, `offScale`, `overProtein`) print **one** warning between
them, never two, however many are true at once. A 400 lb visitor trips both 6 and 7 and sees a
single line. None of the three alters a number: `mcCalc`'s arithmetic is identical to the version
before them, verified across 737,280 input combinations with every numeric field compared.

## Worked examples

Regenerated for this document, not copied from anywhere. `mcCalc` was extracted verbatim
from `site-src/_script.html` and executed directly. Each profile was then put through the
live source calculator at <https://macro-calculator-xi.vercel.app/> two ways: by running
its own `calculate()` function against a DOM stub, and — for profiles 1, 4, 5 and 6 — by
driving the rendered page in a real browser and reading the printed results. Both agreed.

**Checked on 2026-09-24.** The live site responded (HTTP 200, 14,036 bytes) and its
`calculate()` matched the constants documented above line for line.

Coverage: both sexes; all four goals; all three protein bases including both `trained`
rates and the small and large `frame` settings; the Devine 5'0" clamp (7 vs 8); the
1,100-calorie floor (6); and the floor landing above maintenance (10).

| # | Sex | Age | Weight | Height | Activity | Basis | Goal | Maintenance | Target | Protein | Fat | Carbs | Flag | vs. live source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | F | 35 | 150 lb | 5'5" | 1.55 | standard | maintain | 2,133 cal | 2,133 cal | 126 g / 504 cal | 71 g / 640 cal | 247 g / 989 cal | — | identical |
| 2 | M | 40 | 200 lb | 6'0" | 1.375 | trained, 1 g/lb | fat loss, 20% (0.8) | 2,551 cal | 2,041 cal | 200 g / 800 cal | 68 g / 612 cal | 157 g / 629 cal | — | identical |
| 3 | F | 28 | 135 lb | 5'2" | 1.725 | better, small (0.95) | muscle gain | 2,235 cal | 2,503 cal | 121 g / 484 cal | 83 g / 751 cal | 317 g / 1,268 cal | — | identical |
| 4 | M | 30 | 185 lb | 5'10" | 1.55 | better, large (1.15) | recomp | 2,798 cal | 2,574 cal | 213 g / 852 cal | 86 g / 772 cal | 238 g / 950 cal | — | identical |
| 5 | F | 60 | 250 lb | 5'0" | 1.2 | trained, 1.2 g/lb | fat loss, 25% (0.75) | 1,951 cal | 1,463 cal | 300 g / 1,200 cal | 49 g / 439 cal | **0 g / 0 cal** | warning (`clamped`) | identical numbers; the source prints the same 0 g with no warning |
| 6 | F | 70 | 100 lb | 5'0" | 1.2 | standard | fat loss, 25% (0.75) | 1,074 cal | **1,100 cal** | 100 g / 400 cal | 37 g / 330 cal | 93 g / 370 cal | floor (`floored`, and `noRoom`) | **differs by design** — source: 806 cal target, 27 g / 242 cal fat, 41 g / 164 cal carbs. Protein and maintenance identical. |
| 7 | F | 30 | 120 lb | 4'11" | 1.2 | standard | maintain | 1,404 cal | 1,404 cal | 100 g / 400 cal | 47 g / 421 cal | 146 g / 583 cal | — | identical |
| 8 | F | 30 | 120 lb | 5'0" | 1.2 | standard | maintain | 1,423 cal | 1,423 cal | 100 g / 400 cal | 47 g / 427 cal | 149 g / 596 cal | — | identical |
| 9 | M | 30 | 240 lb | 5'10" | 1.55 | standard | maintain | 3,185 cal | 3,185 cal | 161 g / 644 cal | 106 g / 956 cal | 396 g / 1,585 cal | — | identical |
| 10 | F | 70 | 95 lb | 4'10" | 1.2 | standard | fat loss, 15% (0.85) | 1,009 cal | **1,100 cal** | 100 g / 400 cal | 37 g / 330 cal | 93 g / 370 cal | floor (`floored`) **and `noRoom`** | not re-checked against the live source; the floor and the flags are ours, and nothing shared with the source changed |

Reading the two edge cases:

- **7 and 8 are the clamp.** 4'11" and 5'0", same weight, same everything else. The
  maintenance figures differ (1,404 vs 1,423) because BMR still uses the real height, but
  the protein target is **100 g in both** — Devine has stopped at five feet.
- **6 is the floor.** Maintenance is 1,074; a 25% deficit asks for 806. Peter's version
  lifts the target to 1,100, recalculates fat and carbs from that lifted figure, and flags
  it. The source hands over 806 calories silently. This is the one row in the table that is
  *supposed* to differ.
- **6 and 10 are both above maintenance.** The lifted target (1,100) is higher than
  maintenance (1,074 and 1,009), so both set `noRoom` as well as `floored`, and the card
  prints the one warning from departure 5 instead of "Floor reached" and the fat-loss goal
  note. 10 is the case that was reported from the live site.

Eight of the first nine profiles match the live source digit for digit, across every
returned field. The ninth differs only in the target and the two macros derived from it,
and only because of departure 1. Profile 10 was added later, from `mcCalc` alone, and has
not been put through the source.

## Known sharp edges

**Standard protein is height-derived only.** On the `standard` basis, protein comes from
ideal bodyweight, which comes from height alone. Two people of the same height get the
same protein target regardless of what they weigh — a 5'10" man is told 161 g at 150 lb,
at 190 lb and at 240 lb (checked, all three). Peter knows this and likes it: for someone
new to training, protein pinned to the frame they are building toward, not the weight
they are carrying, is the point. The `trained` basis is the one that uses actual
bodyweight. Anyone tempted to "fix" this should read this paragraph first — it is a
decision, not an oversight.

**The source has no floor and no warnings.** Departures 1, 2 and 5 exist only here. A number
checked against the source at a low target or an over-committed macro split will not
match, and should not. Every other comparison should match exactly; if one does not, the
implementation has drifted and the table above is the regression test.

**The source's 5'0" clamp is the same clamp, but untested there.** Both calculators carry
`Math.max(heightInTotal - 60, 0)`, so both stop at five feet. Profiles 7 and 8 confirm
the behaviour on both sides. No claim is made here about what the source's *author*
intended by it.

## Provenance of this document

The specification that originally recorded this was written to a scratch folder under
`/private/tmp` and was removed by system cleanup. The implementation survived; the
document did not. This is a reconstruction, written by reading the shipped code and
re-verifying it against the live source, and it lives in the repository so it cannot be
lost the same way.

`mcCalc`'s body was byte-identical across the first three commits in which it existed —
`20a17a3`, `ca4b185` and `24defd5`, sha1 of the block `4abab7f8…`. It has been edited once
since, on branch `raw4/calculator`, to add the `noRoom` flag and the comment above it: the
block is now sha1 `34d0faf1…`. **No arithmetic changed in that edit**, and it was checked
that way rather than asserted — the old and new blocks were both extracted and run over
426,240 input combinations (both sexes, every whole inch from 4'0" to 7'0", eight weights,
five ages, all four activity levels, all six protein-basis settings, all four goals with
all three deficit settings), and every returned field except `noRoom` matched on every one.

## Re-verifying this

The whole check is repeatable without any test infrastructure:

1. Pull `mcCalc` out of `site-src/_script.html` by slicing between `function mcCalc(v){`
   and the `/* mc:end */` marker, and evaluate that string. Do not retype it; the point
   is to run the shipped bytes.
2. Fetch <https://macro-calculator-xi.vercel.app/>, slice out its single `<script>`, and
   run it against a stub `document` that answers `getElementById` and
   `querySelectorAll('#xSeg button')`. Its segmented controls are plain buttons with
   `onclick` handlers and `data-val` attributes, so calling `.onclick()` sets its state
   the way a click would. Then call `calculate()` and read the output elements'
   `textContent`.
3. Run both over profiles 1 to 9 above and compare every field as a string. `floored`,
   `clamped` and `noRoom` have no counterpart in the source; they are Peter's, and they are
   not part of that comparison.

If the live site is unreachable or has changed, say so rather than presenting the table
as re-verified. The numbers in the table are true of `mcCalc` regardless — that half can
always be re-run offline — but the "vs. live source" column has a date on it for a reason.
