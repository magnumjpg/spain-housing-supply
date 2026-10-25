# LIMITATIONS.md

The list is ordered by how much damage each item does to the conclusions.

---

## 1. The design cannot identify a causal effect of land classification

Land classification is chosen by the municipality. It responds to expected
demand, geography, landowner structure, local politics and the 2008 crash. The
cross-section therefore estimates a equilibrium relationship, not a treatment
effect.

The panel with municipality FE removes time-invariant municipal traits, but the
land measure is a snapshot, so only its interaction with population growth is
identified. A municipality that reclassifies land *because* rents are rising is
indistinguishable from one whose rents rise *because* it reclassified.

**Consequence:** every coefficient in this project is an association. The README
uses "associated with", never "causes".

---

## 2. The treatment is measured after part of the outcome

The SIU workbook used here is dated 2026 (image years mostly 2020–2025). Rents
run to 2024, and the panel starts in 2013. The land classification observed is
therefore partly the *result* of the housing market being measured.

This is a genuine problem, not a stylistic caveat. It would bias the
cross-section towards finding that places with more development land have higher
rents — which is exactly the positive sign observed. That is one reason the
positive coefficients are not interpreted as evidence against the restriction
hypothesis.

A historical SIU series or a reconstructed panel of plan changes would fix this.
Neither is available in the current release.

---

## 3. The land measure is coarse

`share_nonurbanizable` is a share of **total municipal area**, not of buildable
or serviceable land. A municipality can be 95% non-urbanizable and still have
abundant flat, serviced land next to its urban core. Another can be 60%
non-urbanizable with every remaining hectare on a slope.

`MunTotSue` includes mountains, rivers, military land and protected natural
parks. The measure conflates "protected" with "unbuildable" with "far away".

The project mitigates this with density and consolidated-urban controls, but does
not solve it.

---

## 4. The outcome is municipal average rent, not the rent of new housing

The hypothesis is about the price effect of releasing land. The data measure the
average rent of the existing stock in a municipality. New-build units are a small
share of that stock, and the rent series is smoothed.

So even a real effect on new-build rents would be diluted towards zero. **The
null result is partly a measurement-resolution result.**

### 4b. The SERPAVI check narrows this concern but does not remove it

Section 2b of the README repeats the cross-section with SERPAVI, a tax-based rent
series that is independent of INE 69330. It reproduces the null: the same two
coefficients are negative and the restriction measures stay insignificant. That
makes it harder to argue that the result is an artefact of one statistical
operation.

It does not fix the resolution problem. SERPAVI is also an average/median of the
existing rental stock, not the rent of new-build units, and it is narrower still:
collective residential buildings, tax declarations, censored small cells, and no
Navarra or Basque Country. Two smoothed stock measures agreeing is evidence about
the stock margin, not about the new-build margin where the hypothesis lives.

---

## 5. `munnvivpnd` is a stock, not a delay

`pending_dwellings` counts dwellings planned in development areas that had not
been materialised when the SIU image was taken. It does not carry a plan date, so
it cannot distinguish:

- planned in 2006, stalled since the crash;
- planned in 2023, not yet due;
- planned, sold, and deliberately phased over 15 years.

The README is explicit about this. The project does **not** claim that the
pending stock is evidence of land hoarding, speculation or obstruction. Those are
hypotheses the data cannot test.

The plan-vintage result (§5 of the README) reinforces the caution: median
pending share falls from 85% for plans under five years old to 58% for plans
over 30 years old. Part of the gap is simply capacity that has not had time to be
built. 74% of the pending dwellings nevertheless sit under plans approved more
than 15 years ago.

### 5b. The 45.7-year ratio is a description, not a forecast

Dividing pending dwellings by recent net additions makes the pipeline legible, but
it is not a projection. Three things push it upward and one pushes it downward:

- the denominator is **net** of demolitions, so gross construction is higher and
  the ratio is an upper bound;
- the 2023–2025 window is short and construction was recovering from a low base;
- part of the pending stock may never be built, which makes the ratio an
  "equivalent supply" figure rather than a queue;
- demand and construction capacity can grow, which would shorten the calendar
  time.

The ratio is therefore reported with its window, its n and its p25/p75, and the
2021–2025 robustness check (34.8 years on 115 municipalities) is shown next to the
headline (45.7 on 359). The claim is "decades, not years", not a date.

---

## 6. The sample is urban and not representative of Spain

431 municipalities, all of them in the INE Urban Indicators universe (roughly,
municipalities above 10,000 inhabitants plus provincial capitals). They hold 15.5
million dwellings, so they cover most of the housing stock, but they are not a
random sample of municipalities.

Rural municipalities, which are the majority by count, are absent. Since the
non-urbanizable share is highest in rural areas, this truncates the very
variation the hypothesis is about.

---

## 7. No income, so no affordability

Rent per square metre is not affordability. A municipality can have high rents
and high incomes. The project cannot compute rent-to-income at municipal level
with these sources, so it does not claim to.

I tried to add municipal income as a control from INE's *Atlas de Distribución
de Renta de los Hogares* (ADRH, table 30824). That table is published at census
tract / district / municipality level in one very large semicolon-separated CSV.
The download obtained here stopped mid-record at 219 MB, so the file could not be
validated or parsed reliably and **no income control is used**. The omission is
recorded rather than papered over: a municipal income control would absorb part
of the urban–rural gradient, which is exactly the variation the non-urbanizable
coefficient is picking up.

---

## 8. SIU coverage is not random

5,898 of ~8,131 municipalities report land classes. Non-reporting is correlated
with not having a general plan and with being small. The SIU aggregate (5.17
million planned dwellings) is therefore a **lower bound** on plan capacity in
Spain, not a national total.

The 5.17 million figure is also specific to development areas
(`areas_desarrollo_mun`). It excludes capacity that exists inside consolidated
urban land through infill and height increases, which is where much of the real
supply response happens in large cities.

---

## 9. Cross-sectional standard errors with 52 clusters

Clustering by province is the right level for planning regimes, but 52 clusters
is on the low side. The p-values should be read as approximate. The two
significant coefficients (pending share, unstarted share) would not survive a
severe multiple-testing correction across the 20 cross-section specifications,
and are not presented as discoveries.

---

## 10. What would actually move the project forward

In order of value:

1. **A historical SIU or a plan-change panel.** Would allow an event study and
   fix the timing problem in item 2.
2. **Cadastral vacant-lot data.** Would separate "not built" from "no demand" at
   parcel level.
3. **Municipal income (ADRH) with a proper crosswalk.** Would turn rent levels
   into affordability.
4. **Building permits at municipal level.** Would replace the SIU stock with a
   flow and give the pipeline a time dimension.

None of these is a robustness check. They are different data.

---

## 11. The comparative chapter is descriptive, and its units are only partly harmonised

Items 1–10 limit the Spanish core. This section limits the international chapter,
which is a benchmarking exercise, not an identification strategy.

### 11.1. Country price series are indices with different construction

The OECD harmonises the series, but the underlying house-price indices are built
from different national sources, with different quality adjustment, different
geographic coverage and different treatment of new versus existing dwellings.
Comparing **changes** is defensible; comparing **levels** is not, which is why the
project never does it. A country whose index covers only major cities can show a
different change from one whose index covers the whole country.

### 11.2. The price samples are not the same size

Price-to-income covers 40 countries, price-to-rent 42, real prices 47 (40 inside
the price-to-income sample). The 2000-to-latest comparison covers only 25, because
11 post-2000 EU members and four non-EU countries (Chile, Iceland, Luxembourg,
Russia) have no 2000 observation. Every rank is reported with its own `n`; a rank
of 7 of 40 is not comparable to a rank of 5 of 25 as if the denominators were the
same.

The endpoint is mixed too: 36 of the 40 price-to-income series reach 2025, while
Israel ends in 2016, Iceland and Russia in 2019, and Colombia in 2024. The headline
median (+9.3%) is therefore a mixed-endpoint median. On the 36 countries that do
reach 2025 it is **+10.6%**, and Spain stays 7th. The mixed endpoint changes the
benchmark by about a point but not the ranking.

### 11.3. Permits are not completions, and the denominator is crude

A permit is a leading indicator. It can be hoarded, delayed, revised or abandoned,
and it does not measure the dwelling that is ultimately built. The ratio is per
1,000 inhabitants, not per household or per existing dwelling, because annual
household counts are not on the same country panel. Countries with declining
population can look better per capita while building less than they need.

### 11.4. Permit coverage is 34 and 33 countries, not the full European sample

Bosnia has permits but no Eurostat population series, so no per-capita value. The
UK permit series ends in 2019, so it is absent from the 2021–2024 window. Kosovo's
population ends in 2022, so it fails the three-observation rule. The chapter
reports the coverage it has, not the coverage the source list implies.

### 11.5. 2025 permits are excluded

Eurostat's 2025 values are preliminary. Spain's 2025 value is exactly 200.0
thousand, against 179.4 thousand in 2024 — a round flash number, not a completed
year. Including it would mix a preliminary estimate with four final years. The
latest complete year is 2024, and 2024 is reported separately as a single year.

### 11.6. The city layer covers six countries, and mixes years

France, Italy and the Netherlands have no comparable Urban Audit rent series, so
the city comparison is six countries, not Europe. Spain's latest city year is
2023, Germany's 2022, Portugal's 2024 and Lithuania's 2025. A common year would
drop Spain or Germany. The year is stored per city; the ratio uses two indicators
from the same city and year, so the mismatch is across countries, not within a
ratio.

The geography is also mixed: Eurostat reports some cities as **greater-city**
aggregates instead of strict municipal boundaries — 44 of the 251 comparable
cities, including Madrid, Barcelona, Valencia, 25 of the 87 Spanish cities and all
16 Portuguese ones. Price and rent come from the same geography, so the ratio is
internally consistent, but "city median" combines two spatial definitions and the
absolute values are not directly comparable to a municipal-boundary series.

The sensitivity is computed, not assumed. Dropping greater-city units leaves 207
cities in five countries (Portugal disappears, because it has no municipal-boundary
city in the source); Spain's median falls to **16.06 years** and its rank becomes
**3rd of 5**, which is the median of that sample. The statement "Spanish cities are
not the most expensive relative to rent" survives; "lower half" does not survive as
a general claim and is only true of the six-country sample.

### 11.7. Rent units are harmonised by a heuristic, and Latvia is excluded

Urban Audit rent values are not unit-harmonised, and Eurostat's label ("average
annual rent per m²") is not reliable across countries: Germany and Portugal report
values of about 8.5 EUR/m², which are plainly monthly, while Spain, Finland,
Croatia and Lithuania report annual values above 82. The label cannot be used as
the rule. The project treats a country as monthly if its median raw rent is below
20 EUR/m², and annual otherwise. The country medians separate cleanly (8.50 and
8.46 monthly; 82.53, 187.91, 129.00 and 113.46 annual), but the rule is a
heuristic, not metadata. Latvia's four cities imply gross yields from 2.3% to
17.8% under a single unit, so Latvia is excluded from the comparable sample. The
raw rent, the unit and the `comparable` flag are in `comparative_cities.csv` so a
reader can redo the rule.

### 11.8. Price-to-rent is a yield, not affordability

The city measure divides purchase price by gross annual rent. It says nothing
about incomes, taxes, maintenance, vacancy or financing costs. A low price-to-rent
can mean cheap housing or expensive rents; the project does not interpret it as
affordability. It is used because city income is stale, not because it is the
better concept.

### 11.9. The ranks are fragile

Spain is 7th of 40 on price-to-income growth, but only **0.2 percentage points**
behind Hungary and about **1.1 points** ahead of Switzerland. It is 28th of 33
on 2021–2024 permits, but only **0.01 dwellings per 1,000** ahead of Montenegro and
0.05 ahead of Latvia. A routine source revision could move Spain several places.
The rank is a communication device, not a precise estimate; the median and the
neighbouring countries are reported next to it for that reason.

### 11.10. The chapter does not compare the pipeline

There is no harmonised cross-country measure of "planned but not built" dwellings.
The 45.7-year ratio is Spanish, built from SIU planned and pending dwellings. The
chapter compares the **flow** (permits) and the **price outcome**, not the stock of
unbuilt permissions. A reader should not read "Spain permits 2.64 per 1,000" as
"Spain has the largest unbuilt pipeline in Europe"; the second claim is not
measured here.

### 11.11. No cross-country causal estimate, by design

Permits, prices, credit, migration and incomes are jointly determined. A
cross-country regression of prices on permits would be a correlation with no
credible exclusion restriction, and country fixed effects would absorb the permit
measure. The chapter therefore reports distributions and ranks and makes no causal
claim. This is a deliberate limit, not an omission.
