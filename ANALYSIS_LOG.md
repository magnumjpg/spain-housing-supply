# ANALYSIS_LOG.md — how the work actually went

Not a polished narrative. A record of what was tried, what broke, and what was
changed as a result. Written so a reader can see the process rather than only the
output.

---

## Session 1 — feasibility

**Goal:** find out whether a municipal land-classification dataset could be
built from public sources at all.

Checked, in order:

1. SIU landing page (`mivau.gob.es/SIU`). Found the alphanumeric ZIP, 6.6 MB.
   Downloaded with `curl` after `Invoke-WebRequest` returned 403. The 403 was not
   a transient error; MIVAU blocks the default PowerShell user agent. Fix:
   browser `User-Agent` on every request.
2. Unzipped. 40 workbooks, national/province/municipality variants. The
   municipality files are the ones that matter.
3. INE table 69330. 160,080 rows, 434 municipalities, 23 indicators, 2010–2025.
   Downloaded as CSV.
4. INE IPVA (59060) and Padrón (29005) for the rent index and population.

**Output of the session:** a green light, and a first list of doubts about the
SIU semantics. The doubts turned out to be the most valuable part.

---

## Session 2 — semantics, or: the seven columns that do not add up

First attempt: sum all seven `MunPr*` columns. Result: row sums between 100 and
151, with a long right tail.

That is the kind of thing that gets quietly normalised away. Instead I read the
official metadata workbooks, which had been sitting in the ZIP unopened.

Findings:

```
MunPrSuCon + MunPrSuNoC + MunPrSuzDe + MunPrSuzNd + MunPrSnUzb + MunPrOtr = 100
MunPrADes = MunPrSuNoC + MunPrSuzDe
```

`MunPrADes` ("development areas") is an **aggregate of two other columns**, not a
seventh class. Summing it double counts. Maximum discrepancy across 5,898 rows:
0.001 percentage points — so the identity is exact, not approximate.

`MunTotSue` is municipal area in km², not hectares and not "total land
classified". Checked against known municipal areas.

**Consequence:** every share in the pipeline is built from the six base classes,
and `share_development_areas` is used as an aggregate, never added to the others.
Two tests now assert both identities.

**Lesson recorded:** the metadata file in an official ZIP is not decoration.

---

## Session 3 — the encoding trap

Merging INE Urban Indicators to the Padrón by name failed for exactly 118
municipalities. Not random: all of them had accented characters.

Cause: the CSV is UTF-8, but the first read used `encoding="latin1"` (a habit
from older INE files). Latin-1 turns `Alcalá` into `AlcalÃ¡`, which normalises to
a different token key.

Fix: read as UTF-8. Matching went from 316/434 to 434/434.

**Second trap in the same file:** numbers are Spanish-formatted
(`1.234.567,8`). `pd.read_csv` with default settings parses `1.234` as `1.234`.
Rents would have been off by three orders of magnitude in some rows and plausible
in others — the worst kind of corruption, because the output still looks like
data. Fixed with an explicit parser, and a test asserts rents fall in a plausible
range.

---

## Session 4 — the code crosswalk

The Urban Indicators CSV has municipality **names but no codes**. The Tempus
JSON API has codes but 87 of them are non-numeric (`ES069C`, `ES503C1`, …).

Built the crosswalk in three layers:

1. Numeric codes used directly (347 municipalities).
2. Non-numeric codes matched by a normalised, article-insensitive token key
   against the 2025 Padrón, accepting only keys unique within the Padrón.
3. Two residual names mapped by hand after inspection:
   `Castelló de la Plana → 12040`, `Palma de Mallorca → 07040`.

The function raises if anything is unmapped. No silent `NaN` merge.

---

## Session 5 — the first regression, and the bad news

Estimated the naive cross-section: log rent on the non-urbanizable share, with
province FE.

```
non-urbanizable share: −0.099  (p < 0.001)
development share:     +0.051  (p = 0.007)
```

Both signs are the **opposite** of the hypothesis. The temptation at this point
is to look for a specification that flips them — log the land measure, drop
Madrid, trim outliers, use price instead of rent.

Instead: what confound would produce this? Answer: rurality. Non-urbanizable
share is highest in rural, cheap municipalities. The relationship is an
urban–rural gradient, not a planning effect.

Added density, consolidated-urban share, population, stock and population
growth:

```
non-urbanizable share: −0.047  (p = 0.21)
development share:     +0.014  (p = 0.45)
```

The effect halved and lost significance. The naive result was a confound.

**Decision point:** the rent hypothesis is not supported. Options were to bury it
or to restructure the project. Chose the latter (DECISIONS.md D3–D4).

---

## Session 6 — reframing

Went back to the SIU descriptive variables that had been downloaded but not yet
used: `munnumviv` (planned dwellings), `munnvivpnd` (pending), `munpradsnu`
(development land not started).

Results on the 431 matched municipalities:

- 5,167,809 planned dwellings; 3,490,428 pending → **67.5%**.
- Median municipal pending share: **72.1%**.
- Planned capacity = **33.4%** of existing stock; pending = **22.6%**.
- **48.8%** of development land not started (area-weighted).
- **35.7%** of municipalities have more than 80% pending.

This is not a subtle statistical result. It is a large, direct measurement, and
it survives the obvious objection ("demand will clear it") because the pending
share in fast-growing municipalities is 71.3% versus 75.1% in declining ones.

The project became about the gap. The rent analysis stayed in, as a documented
failed identification attempt with a figure showing why the naive result is
misleading.

---

## Session 7 — panel, and a result that did not survive

Built the 2013–2024 panel with municipality FE and interacted the land measures
with population growth.

With year FE:

```
non-urbanizable × growth:  −0.073  (p = 0.15)
planned capacity × growth: −0.098  (p = 0.008)
```

With province-year FE (absorbing regional shocks):

```
non-urbanizable × growth:  −0.099  (p = 0.008)
planned capacity × growth: −0.028  (p = 0.26)
```

The planned-capacity result **disappears** once province-year shocks are absorbed.
That is a fragile result and is reported as fragile. The non-urbanizable
interaction moves the other way, which is also not a clean story.

Did not chase either. The README says the panel is a check, not an elasticity.

---

## Session 8 — figures

Seven figures. Two rounds of review:

- Round 1: fig 5 (top pending municipalities) had the "% pending" labels printed
  on top of the bars, unreadable, and no legend. Fixed by placing labels after
  the full bar and adding a legend.
- Round 2: fig 2 had no correlation annotation; added `r = 0.14` so the "weak
  responsiveness" claim is visible rather than asserted. Fig 3 legend moved off
  the confidence intervals.
- Grid set below data (`axes.axisbelow`) so bars are not cut by grid lines.

Figure 4 is the important one: raw slope on the left, residualised flat
relationship on the right. It is the visual form of the project's main caveat.
Figure 7 was added later, after the plan-vintage check, and does the same job for
the pipeline finding.

---

## Session 9 — external validation and the plan-vintage check

Two additions after the first full draft.

**External validation.** MIVAU publishes its own national aggregate in
`areas_desarrollo_nac.xlsx`. Read it rather than trusting our own sum: 5,900
municipalities, 9,600,382 planned dwellings, 7,090,504 pending (73.9%), 55.9% of
development land not started. Our 431 municipalities are 53.8% of the national
planned stock and 49.2% of the pending stock. The national pipeline is slightly
more unbuilt than the urban sample, which is reassuring: the sample is not
cherry-picked and the 5.17 million figure is a subset, not a rival estimate.

**Plan vintage.** A reader could reasonably object that "pending" is trivially
driven by plan age. Checked it: the correlation between plan age and pending
share is −0.36, and median pending share falls from 85% (plans ≤5 years) to 58%
(plans >30 years). So the objection has force. Added a section, a figure and a
table. The counter-counter is that 74% of pending dwellings sit under plans older
than 15 years, so the gap is not *only* recent plans. Both facts are now in the
README, adjacent, instead of one being used to defeat the other.

---

## Session 10 — documentation and tests

Wrote `DATA.md`, `METHOD.md`, `LIMITATIONS.md`, `DECISIONS.md`, `RED_TEAM.md`
and this log. Rationale: the analysis is only as credible as the record of the
choices behind it.

Tests (13, all passing):

- land shares sum to 100 (six base classes);
- `MunPrADes` equals the sum of its two components;
- pending ≤ planned;
- unique municipality-year;
- positive rents, prices, stock, population;
- sample size floor;
- bounded shares;
- pipeline aggregates internally consistent;
- `results.json` has all required sections;
- every regression has finite coefficient, positive SE, p in [0,1];
- the sample is a strict subset of MIVAU's national aggregate;
- plan vintage is documented and its sign is as claimed;
- README exists and contains the limitations section.

---

## Session 11 — the rent null gets a second source, and income does not

**SERPAVI.** Before publishing, the weakest point was that the rent null rested on
one series. Downloaded MIVAU's SERPAVI workbook (71 MB, six sheets), parsed only
the 2024 municipality block, and repeated the same five specifications with its
median monthly rent per m². All 431 municipalities have a SERPAVI rent; 406 also
have an INE rent; the correlation is 0.991 in levels and the annualised median
ratio is 0.959.

The coefficients reproduce the INE result: non-urbanizable −4.0% (p=0.27),
development land +1.1% (p=0.57), planned capacity +3.5% (p=0.15), pending share
−2.4% (p=0.003), unstarted share −2.2% (p=0.031). This is the first time the
project has an independent measurement of the outcome, not just a different
specification of the same measurement. It makes the null harder to dismiss as an
INE artefact. It does not touch the endogeneity problem, and the docs say so.

Two parsing traps: the workbook uses one column block per year (the 2024 columns
end in `_24`), and the `Municipios` sheet has 284 columns, so reading it whole is
wasteful. Reading only the seven needed columns takes ~15 s.

**ADRH income.** Also tried to add municipal income from INE table 30824. The
download is a census-tract-level CSV; the file obtained here stopped mid-record
at 219 MB. Checked the tail rather than assuming success, found the truncation,
and dropped the control. Recorded as D16 and in LIMITATIONS §7. The honest
position is that income remains an omitted confounder, not that it was controlled.

**Tests.** 15 now: two SERPAVI-specific ones (cross-source agreement and
reproduction of the negative coefficients) plus the previous 13.

---

## Session 12 — the project was reading as "unsolvable", so the framing changed

The first published draft led with the rent null. That was defensible as honesty
but wrong as a presentation of the work: it made the project sound like a failed
test rather than a finding. The rent null is a failed identification in one
design; the pipeline is a large, measurable fact.

Added a **stock-over-flow ratio**: pending dwellings divided by the 2023–2025 net
annual change in the Catastro dwelling stock. Across 359 municipalities, 3.17 M
pending dwellings against 69,411 net additions per year gives **45.7 years** of
equivalent supply; the median municipality has **48.3 years** and 76% are above
20 years. The 2021–2025 window on 115 consistently-covered municipalities gives
34.8 years. Both are in the README, with the caveat that net additions understate
gross construction and that the ratio is not a forecast.

Rewrote the README around that: finding first, rent test second, with a plain
explanation of why the cross-section cannot identify the rent effect. The null has
not moved; its place in the argument has. `figures.py` unchanged except for the
table export (`outputs/tables/absorption.csv`).

One data trap: Catastro stock coverage jumps from 119 to 399 municipalities in
2023. A 2015–2024 window would silently restrict the sample to large cities, so
the headline uses the short post-2023 window and the long window is a robustness
check, not the main estimate.

---

## Session 13 — the comparative chapter, and three bugs that only appeared when writing it down

**Why.** The Spanish core had a large number (45.7 years) and no external scale.
A reader could not tell whether that was a lot. The obvious fix was a cross-country
comparison. The constraint was to keep it a chapter, not a fourth project, and to
widen it beyond Spain–US.

**Feasibility, in order.**

1. **OECD Analytical House Prices** via the SDMX API. One CSV, 937 KB, 1990–2025,
   annual. It carries price-to-income (`HPI_YDH`), price-to-rent (`HPI_RPI`) and
   real prices (`RHP`) as indices with base 2015. This became the country price
   layer.
2. **Eurostat building permits** (`sts_cobp_a`, `BPRM_DW`, `CPA_F41001_X_410014`,
   `THS`) and population (`demo_pjan`). This became the country supply layer.
3. **Eurostat Urban Audit** (`urb_clivcon`: `SA1053V` price, `SA1049V` rent,
   `DE3017V` population). This became the city layer.
4. **City price-to-income.** Attempted first because it is the natural
   affordability measure. Abandoned when the Urban Audit income series turned out
   to stop in 2019/2020. Comparing 2023 prices with 2019 incomes, in different
   years for different countries, is not a comparison. Switched to city
   price-to-rent.
5. **US ACS city prototype.** Built only to test whether a city comparison with
   income was feasible. It was, but it would have made the chapter a US project
   and required a different tenure/rent definition. Dropped from the chapter.

**Bug 1 — OECD aggregates inflated the sample and changed the ranks.** The first
pass kept every `REF_AREA`, including `EA`, `EA17`, `EA19`, `EA20`, `EU27_2020`
and `OECD`. That gave "7th of 43" on price-to-income and "5th of 28" on
price-to-income since 2000. Dropping the aggregates gives **7th of 40** and
**5th of 25**. The medians moved too (9.3% and 23.7%). This is the kind of error
that makes a rank look more impressive and less true.

**Bug 2 — the permit sample was 33, not 38.** The raw Eurostat permit file has 42
geographies, of which four are aggregates. Several countries then lose a window:
Bosnia has permits but no Eurostat population series; the UK permit series ends in
2019; Kosovo's population ends in 2022. Requiring at least three annual
observations with a matching population gives **34 countries for 2015–2019** and
**33 for 2021–2024**. The README reports those denominators, not the raw 38.

**Bug 3 — rank direction and the city denominator.** Found while drafting the
summary table, not while coding the analysis. Country ranks were "1 = highest",
but the city rank was ascending, so Spain's "3" meant third-lowest while every
other "3" would have meant third-highest. The city rank was also printed against
`n = 87` (Spanish cities) when it was computed across **six country medians**.
Fixed by making every rank descending, adding `rank_direction` and `rank_n`, and
ranking the city row among the six countries. Spain is **4th of 6** (1 = highest
price-to-rent), which is the third-lowest. The prose says "lower half", which is
true under either reading.

**Other traps.**

- **2025 permits are preliminary.** Spain's 2025 value is exactly 200.0 thousand,
  against 179.4 thousand in 2024. Excluded. The permit windows are 2015–2019 and
  2021–2024.
- **City rent units are not harmonised, and the label is wrong.** Eurostat labels
  the rent series "average annual rent per m²" for every country, but Germany
  (8.50) and Portugal (8.46) are plainly monthly, while Spain (82.53), Finland
  (187.91), Croatia (129.00) and Lithuania (113.46) are annual. Rule: median below
  20 → monthly ×12. Latvia's four cities imply yields from 2.3% to 17.8% under a
  single unit, so Latvia is excluded as internally inconsistent.
- **City years are mixed.** Spain's latest city year is 2023, Germany's 2022,
  Portugal's 2024, Lithuania's 2025. A common year would drop Spain or Germany.
  The year is stored per city and the limitation is stated.
- **OECD indices are not levels.** The chapter compares 2015→latest and
  2000→latest changes, never levels. Real prices are ranked inside the
  40-country price-to-income sample, not the 47-country real-price set.

**What the chapter found.**

- Spain's price-to-income rose **25.9%** 2015→2025 (7th of 40; OECD median 9.3%)
  and **56.3%** 2000→2025 (5th of 25; median 23.7%). Price-to-rent rose **58.9%**
  (10th of 42; median 30.3%); real prices **43.0%** (15th of 40; median 38.0%).
- Against its own history, Spain is **17.4% below** its 2007 price-to-income peak,
  **1.9% below** its price-to-rent peak and **12.8% below** its real-price peak.
  The ratios disagree, which is itself the finding: the income denominator has
  improved more than the rent denominator. The two indices are not decomposed into
  each other because the rent index is a national deflator, not the municipal rent
  series.
- Permits: **1.40** per 1,000 in 2015–2019 (31st of 34; median 4.12) and **2.64**
  in 2021–2024 (28th of 33; median 4.62). 2024 is 3.69; the 2006 peak was 16.70.
  Spain now permits about 57% of the European median and 16% of its own 2006 peak.
- Cities: **251** comparable across six countries, **87** Spanish. Spain's median
  price-to-rent is **16.56 years** (p25 14.84, p75 18.59), **4th of 6** on a
  1 = highest rank. Finland 13.41, Lithuania 15.34, Spain 16.56, Portugal 20.81,
  Croatia 21.32, Germany 29.48. Madrid 22.13, Barcelona 23.15, Palma 24.80,
  Eivissa 28.83.

**Figure review.** `fig8` needed a note because the OECD median line is computed
over a changing country set (25 in 2000, 40 in 2025); the note is in the figure
footer. `fig9` needed integer year ticks; `fig10` had overlapping Barcelona and
Palma labels and a country-name axis that was being truncated to two-letter codes.
Three review rounds.

**Tests.** 18 comparative tests, **34 total**. They assert the 40/42/40 price
samples, the 34/33 permit coverage, the 25-country 2000 sample, the 2007 peak
anchors, the 255/251/87/4 city counts, the country-level rent-unit rule, Latvia's
exclusion, the nine-row summary, the bridge to the Spanish pipeline, and that no
NaN leaks into the JSON.

**Honest note.** The comparative chapter does not make the Spanish pipeline look
more exceptional; it makes the *flow* look low and the *price* look high but not
extreme, and it shows Spanish city price-to-rent is in the lower half of the six
comparable countries. That is a more useful result than a Spain-vs-US story that
would have been guaranteed by construction.

---

## What I would do differently

1. **Read the metadata before the first regression.** Two sessions were spent on
   a semantic error that the metadata workbook answered in one page.
2. **Build the code crosswalk before any merge.** Name matching should have been
   the first thing, not the thing that broke the first merge.
3. **State the falsification condition up front.** "If the adjusted coefficient
   is not negative and significant, the hypothesis is not supported" would have
   made the reframe faster and less uncomfortable.
4. **Do not download IPVA if it is not going to be used.** It is cached and
   documented as unused, which is fine, but it is dead weight in the manifest.

---

## Honest summary of the result

The project set out to measure a "permission premium" and did not find one. It
found something else that is measurable and large: a housing pipeline that is
two-thirds unbuilt, in shrinking and growing municipalities alike. The rent null
is reported with the same prominence as the pipeline finding, because a reader
who only sees the positive result would be misled about what the data can
support.
