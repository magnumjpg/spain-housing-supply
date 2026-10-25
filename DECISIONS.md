# DECISIONS.md — the choices, including the ones that cost me the original story

Chronological. Each entry says what was decided, what the alternative was, and
why.

---

## D1. Build on SIU + INE + Padrón, not on Idealista or a scraped portal

**Chosen:** official MIVAU land data + INE rent and population.
**Alternative:** Idealista/Fotocasa listing data, which is richer and more
granular.
**Why:** licensing, reproducibility and the ability to publish the pipeline. A
scraper that breaks in six months is not a portfolio asset. The cost is that
rents are annual municipal averages rather than listing-level, which is a real
limitation and is stated as such.

---

## D2. The unit of analysis is the municipality, not the parcel or the sector

**Alternative:** `tabla_sectores.xlsx` has 68,207 sectors with land class, use,
surface and buildability.
**Why not:** sectors do not map to rents. There is no rent outcome at sector
level. The municipal level is the finest geography where land classification and
a price outcome coexist.
**Cost:** all the aggregation problems in LIMITATIONS.md §3 and §4.

---

## D3. The hypothesis was stated before looking, and then reported as failed

The original framing was *"more classified development land → lower rents"*. That
was written down in the project charter before estimation.

The first run produced:

- raw correlation non-urbanizable share vs log rent: **−0.55** (wrong sign for
  the restriction story, and suspiciously large);
- development share vs log rent: **+0.30** (also wrong sign).

**Decision:** do not go looking for a specification that rescues the sign. Add
the controls that the confound obviously requires (density, consolidated urban
share, province FE) and report what happens. What happened is that the
coefficients collapsed to −0.05 and +0.01, insignificant.

**This is the most important decision in the project.** The alternative — trying
log specifications, dropping outliers, adding controls until the sign flipped —
would have produced a publishable-looking result and a dishonest one.

---

## D4. The headline moved from rents to the pipeline gap

Once the rent hypothesis failed, there were two options: bury the null in a
robustness table, or make the project about what the data actually show.

**Chosen:** make the project about the gap between planned and materialised
housing, and report the rent null prominently as a finding about identification.

**Why:** the gap is large (3.49 million dwellings, 67.5% of planned capacity),
measured directly, and not explained by demand growth. It is a real result. The
rent null is also a real result, and more useful to a reader than a fake positive.

---

## D5. No Monte Carlo, no synthetic counterfactual, no welfare triangle

The previous zoning project (audited separately) used a synthetic data-generating
process and a welfare calculation. Both were removed here.

**Why:** a synthetic DGP can produce any result the author wants, and a welfare
triangle requires an elasticity this design cannot estimate. Including either
would make the project look more sophisticated and be less true.

---

## D6. Province FE, not municipality FE, in the cross-section

Municipality FE would absorb the land measure entirely, since it is
time-invariant. Province FE is the finest fixed effect that leaves variation.

**Cost:** unobserved within-province heterogeneity (coastal vs inland, tourism vs
industry) remains. Coastal and size robustness checks are reported in
`outputs/tables/robustness.csv`.

---

## D7. Cluster standard errors by province

**Alternative:** robust SEs, or clustering by municipality (impossible in a
cross-section).
**Why province:** planning law and housing markets are regional. 52 clusters is
low but defensible; the limitation is stated.

---

## D8. Standardise measures to z-scores for the coefficient plot

The five measures have incomparable units (share of area, dwellings per 1,000).
Plotting raw coefficients on one axis would be meaningless. z-scores make "one
standard deviation" the common unit; the underlying per-percentage-point
coefficient is also stored in `results.json` for share measures.

---

## D9. Keep 2024 as the cross-section year even though 2025 is present

2025 rents are empty (year not closed). 2024 has 408 of 434 rent values and is
the latest complete year.

---

## D10. Drop 2025 from the panel's usable range but keep the rows

The panel runs 2010–2025 because population is available for 2025 and some
outcomes are too. The rent regressions naturally drop 2025 rows due to missing
rent. Filtering the panel would hide the coverage asymmetry; keeping it and
letting the estimators drop rows is more transparent. `coverage.json` reports
both the panel span and the non-missing counts.

---

## D11. Do not publish a national total of planned dwellings

It is tempting to say "Spain has 5.17 million planned dwellings". That number is
the sum over the 431 urban municipalities in the matched sample, not Spain. The
README says "in these 431 municipalities" every time. A national figure would
require the full 5,898-municipality SIU with a stock denominator, which is a
different calculation.

---

## D12. Manual code mappings are allowed, silent drops are not

Two municipality names did not match the Padrón token key. They were mapped by
hand and the mapping is in `config.py` with a comment. If any name fails to map,
`build_panel.py` raises. The alternative — `how="left"` and a silent NaN — is how
municipal datasets lose 20% of their rows without anyone noticing.

---

## D13. Report the plan-vintage result, which weakens the headline

After the pipeline finding was written up, a check on plan age showed that newer
plans have a much higher pending share (r = −0.36; 85% pending for plans ≤5 years
old, 58% for plans >30 years). This is a competing explanation for the gap and it
partially undermines the "paper housing is a problem" framing.

**Chosen:** put it in the README as section 5, add a figure, and state the
counter-fact (74% of pending dwellings sit under plans older than 15 years). Do
not bury it in a robustness table.

**Alternative rejected:** controlling for plan age in the regressions and
reporting only the adjusted gap. That would turn an honest limitation into a
footnote, and the reader would not see that the simplest explanation for part of
the gap is time.

---

## D14. Use `requests`, not PowerShell `Invoke-WebRequest`, for MIVAU

MIVAU returns 403 to `Invoke-WebRequest` and to the default Python user agent.
`requests` with a browser-like `User-Agent` works. This is documented in
`config.py` because it will bite anyone reproducing the work.

---

## D15. Add SERPAVI as an independent outcome, not as a second national estimate

**Context.** The central claim is a null: land classification does not predict
rents once urbanisation is held constant. A single rent series, INE 69330, is a
thin basis for that claim. A reviewer could reasonably ask whether the null is an
artefact of that series.

**Decision.** Add SERPAVI (MIVAU's tax-source rent index, *Modelo 100*) as a
second outcome for the same five cross-section specifications. Report the two
series side by side, plus the cross-source correlation and the annualised ratio.

**Alternatives rejected.**

- *Average the two series into one outcome.* They are different statistics
  (mean annual rent vs median monthly rent of collective buildings) with
  different sample frames. Averaging would hide the disagreement instead of
  showing it.
- *Replace INE with SERPAVI.* SERPAVI excludes Navarra and the Basque Country,
  censors small cells, and covers only collective residential buildings. It is
  narrower, not better.
- *Treat the high correlation as validation of the analysis.* It validates the
  rent *measurement*, not the design. The endogeneity problem is untouched.

**Consequence.** The null reproduces almost coefficient for coefficient
(pending −2.4%, p=0.003; unstarted −2.2%, p=0.031). The docs must still say that
both series measure the stock margin, not new-build rents.

---

## D16. Do not use ADRH income: the download could not be validated

**Context.** Municipal household income would be a useful control, because the
non-urbanizable share is partly a rurality proxy. INE's ADRH (table 30824) is
the obvious source.

**Decision.** Attempt the download, inspect it, and **do not use it** if it
cannot be validated. The published CSV is a census-tract / district /
municipality table. The file obtained here is 219,410,432 bytes and ends
mid-record (`... Renta neta media por hoga`), with no usable row terminator; a
municipal-only extract would require a different API query or a much larger
download. It is not parsed, and no income control is claimed.

**Alternatives rejected.**

- *Parse the truncated file anyway.* A silent partial sample of municipalities
  would be worse than no control: it would look like a complete specification.
- *Substitute provincial income.* That is absorbed by the province fixed effects,
  so it adds nothing to the identifying variation.
- *Use the ADRH file's municipal rows without checking completeness.* The tail
  check is the whole point; an unchecked 219 MB file is not evidence.

**Consequence.** The README and LIMITATIONS say explicitly that income is not
controlled. The income gradient remains a competing explanation for the
non-urbanizable coefficient. The partial file is deleted from `data/raw/` so it
cannot be mistaken for an input.

---

## D17. Report years of pending supply, not only a percentage

**Context.** "67.5% of planned dwellings are pending" is accurate but hard to
feel. A percentage does not distinguish a pipeline that is large relative to
demand from one that is large in absolute terms but absorbable.

**Decision.** Divide pending dwellings by the recent net annual change in the
Catastro housing stock, municipality by municipality, and report the aggregate
and median years. Use 2023–2025 for the headline because Catastro coverage
expands from 119 to 399 municipalities in 2023; report 2021–2025 on the smaller
consistently-covered set as a robustness check.

**Alternatives rejected.**

- *Divide by planned dwellings or by stock.* Both are already in the README and
  neither is time-interpretable.
- *Use building permits (licencias).* A better denominator, but it requires
  another MIVAU download and a municipal crosswalk; the stock change is already
  in the INE panel and is adequate for an order of magnitude.
- *Average the municipal ratios.* Would let tiny municipalities dominate. The
  headline is `Σ pending / Σ additions`; the median is reported separately.

**Consequence.** The headline becomes **45.7 years** (median 48.3, p25–p75
20.9–136.3) on 359 municipalities, with a 34.8-year robustness check on 115. The
limitations are explicit: net rather than gross additions, a two-year window, and
a stock that may never be built. The number is an equivalent-supply description,
not a forecast.

---

## D18. The international comparison is a chapter inside 01, not a fourth project

**Context.** After the Spanish pipeline was established, the obvious next question
was whether Spain is unusual. That could be built as a separate cross-country
project.

**Decision.** Build it as a **chapter inside `01_housing_land_power`**, sharing
its README, tests and `results.json`. The portfolio stays at three projects, one
per CV face.

**Alternatives rejected.**

- *A fourth project "Spain vs Europe".* It would repeat the same question in a
  thinner design, create a second housing project competing with the first, and
  break the "no flagship, one project per CV face" rule. It would also imply that
  the comparison stands on its own, when its only purpose is to dimension the
  Spanish result.
- *A separate repository that 01 links to.* Same duplication with more maintenance
  and two sets of documentation that can drift.

**Consequence.** The chapter is scoped by the Spanish question: it compares the
two margins that can be harmonised (price changes and permit flows), not
everything that could be compared. The 45.7-year pipeline remains Spain-only
because no cross-country equivalent exists.

---

## D19. Multi-country and Spain-centred, not Spain vs the United States

**Context.** The first feasibility sketch was a Spain–US comparison, with US
metropolitan areas as the city layer. The user's requirement was explicit: widen
the comparison to more countries, and do not turn the project into a US project.

**Decision.** Use the full OECD country sample (40 countries with price-to-income,
42 with price-to-rent), the full European permit sample (34 and 33 countries), and
a six-country city sample. The United States is one observation in the OECD
distribution, not the organising axis.

**Why.** A bilateral comparison makes Spain look like an outlier by construction:
the reader cannot tell whether the difference is Spain, the comparator, or the
pair. A distribution gives Spain a rank and a median, and shows that several
countries are above it. It also avoids importing US-specific institutions
(property tax, zoning, mortgage market) into a Spanish land question.

**Cost.** The city layer shrinks to six countries because Eurostat Urban Audit
rent data are missing for France, Italy and the Netherlands. The US ACS city
prototype was built only to test feasibility and does not drive the chapter.

---

## D20. Three layers with different units; compare changes, never levels

**Context.** "Compare Spain with other countries" can mean levels, changes or
institutions. Only one of those is defensible with these data.

**Decision.** Three layers:

1. **Country prices** — OECD indices, 2015 = 100. Compare 2015→latest and
   2000→latest changes only.
2. **Country supply** — Eurostat building permits per 1,000 inhabitants, window
   means for 2015–2019 and 2021–2024.
3. **City price-to-rent** — Urban Audit purchase price divided by annual rent per
   m², in years of gross rent.

**Why not levels.** The OECD publishes indices, not price-to-income levels. Even
if levels were available, cross-country levels embed different definitions of
income, housing quality, taxation and imputed rent. Comparing index changes is
still imperfect, but it removes the level problem and matches what the source
actually measures.

**Why permits per 1,000 and not per household.** Household counts are not
available on the same annual country panel; population is. Per capita is a
cruder denominator, but it is consistently measured and adequate for an order-of-
magnitude comparison. A per-dwelling or per-household version would be better and
is listed as a limitation.

---

## D21. The city layer uses price-to-rent, not price-to-income

**Context.** The natural city measure is price-to-income. Eurostat Urban Audit has
city income, but the series stops in 2019/2020. Using it would compare 2023
Spanish house prices with 2019 Spanish incomes, and 2022 German prices with 2020
German incomes — a different vintage problem in every country.

**Decision.** Use **price-to-rent**: average apartment purchase price divided by
average annual rent per m², both from the same city and year. Report it as years
of gross rent.

**Alternatives rejected.**

- *City price-to-income with stale income.* Rejected: the numerator and
  denominator would be five years apart, and the gap differs by country.
- *Drop the city layer.* Rejected: it is the only subnational comparison, and it
  produces a genuinely surprising result that belongs in the chapter.
- *Use national income as a proxy.* Rejected: it would turn a city measure into a
  country measure with city prices, and city income dispersion is the point.

**Cost.** Price-to-rent is a yield, not affordability. A low ratio can mean cheap
housing or expensive rents. The README says this explicitly and does not convert
the ratio into an affordability claim.

---

## D22. Harmonise city rent units per country; exclude Latvia

**Context.** Urban Audit rent values are not unit-harmonised. Eurostat's label says
"average annual rent per m²" for every country, but the German and Portuguese
values (about 8.5 EUR/m²) are plainly monthly, while the Spanish, Finnish, Croatian
and Lithuanian values are annual. Taking the label at face value would make German
cities look 12 times cheaper relative to rent.

**Decision.** Compute the **country median raw rent**. If it is below 20 EUR/m²,
treat the country as monthly and multiply by 12; otherwise treat it as annual.
Then check within-country consistency. Exclude Latvia, whose four cities imply
gross yields from 2.3% to 17.8% under a single unit.

**Why a country-level rule.** Rent units are a reporting convention, not a
city-level choice. A per-city rule would fit the data rather than the metadata and
would let the ratio determine its own units. The country medians separate cleanly:
Germany 8.50 and Portugal 8.46 on the monthly side; Spain 82.53, Finland 187.91,
Croatia 129.00 and Lithuania 113.46 on the annual side. The 20 threshold sits in
an empty interval between 8.5 and 41.4.

**Alternatives rejected.**

- *Infer the unit from the implied yield.* Circular: the yield is the output.
- *Use the metadata label.* It says annual for every country, which is
  contradicted by the German and Portuguese magnitudes.
- *Drop all rent-based comparison.* Loses the only city layer and the most
  interesting counterweight in the chapter.

**Consequence.** 251 of 255 cities are comparable; Latvia's four are flagged and
excluded from medians and figures. The rule could misclassify a country whose
rents cluster near 20 EUR/m²; none currently does, and the raw medians are stored
in `comparative_cities.csv` so the rule can be audited.

---

## D23. Descriptive benchmarking, not causal identification; ranks inside samples; 2025 permits excluded

**Context.** With 33–42 countries, it is tempting to regress prices on permits and
report a cross-country "regulation effect". That regression would be uninterpretable:
permits and prices are jointly determined by demand, credit, migration, income and
construction capacity, and the countries differ in measurement.

**Decision.** The chapter reports **distributions, medians and ranks**, not
coefficients. Three rules protect the comparison:

1. **Ranks are computed inside the sample the metric is compared on.** Real house
   prices are ranked within the 40-country price-to-income sample, not the
   47-country real-price-only set. The 2000 comparison reports n = 25, not 40.
2. **The rank direction is explicit.** Every row of `comparative_summary.csv`
   carries `rank_direction = "1 = highest"` and a `rank_n` denominator. The city
   row is ranked among six country medians, not among 87 Spanish cities.
3. **2025 permits are excluded.** Spain's 2025 value is exactly 200.0 thousand
   against 179.4 thousand in 2024; a preliminary round number would contaminate
   the 2021–2024 window.

**Alternatives rejected.**

- *A cross-country regression with country fixed effects.* There is no panel
  dimension that would identify a regulation effect; country FE would absorb the
  permit measure.
- *A "regulation index" from OECD/World Bank indicators.* Different concept,
  different year, and it would invite a causal reading the design cannot support.
- *Keep 2025 because it is the latest.* The value is preliminary and visibly
  rounded; using it would trade honesty for recency.

**Consequence.** The chapter's claims are of the form "Spain is 7th of 40 on this
change" and "Spain permits 2.64 per 1,000 against a median of 4.62", never "permits
cause prices". The ranks are reported with their n, their medians and the
neighbouring countries, because the rank is fragile: Spain is 0.2 percentage
points **behind** Hungary on price-to-income growth and 0.01 dwellings per 1,000
**ahead** of Montenegro on 2021–2024 permits.

---

## D24. Keep greater-city aggregates in the city layer, and say so

**Context.** Eurostat Urban Audit publishes some units as municipal boundaries and
others as "greater city" aggregates. In the comparable sample, 44 of 251 are
greater-city units, including Madrid, Barcelona, Valencia, 25 of the 87 Spanish
cities, all 16 Portuguese cities, 2 German and 1 Croatian.

**Decision.** Keep both, with the geography left as Eurostat publishes it, and
state the mix in `DATA.md` §6.4 and `LIMITATIONS.md` §11.6.

**Alternatives rejected.**

- *Keep only municipal-boundary cities.* It would drop **every Portuguese city**,
  Madrid, Barcelona and Valencia — that is, most of the sample's large Spanish
  cities and one of the six comparison countries. The resulting "Spanish cities"
  would be a set of small and medium municipalities.
- *Force greater-city units onto municipal boundaries.* The underlying indicators
  are published at the greater-city level; there is no public crosswalk that would
  let the project rebuild municipal values without new data.

**Why it is acceptable.** The ratio uses price and rent from the same geography, so
it is internally consistent for every city. What the mix rules out is treating the
absolute city medians as municipal-boundary values or comparing them with a
municipal series. The country medians are also robust in direction: Germany's gap
to Spain is 13 years, and Portugal's median is 4.3 years above Spain's despite
being entirely greater-city units.

**Cost.** A reader who wants strict municipal comparability cannot get it from this
source. The `city_name` column preserves the "(greater city)" suffix, so the subset
can be filtered.

**What the sensitivity shows.** It is not cosmetic. Dropping greater-city units
leaves 207 cities in five countries (Portugal has none on a municipal boundary),
Spain's median falls from 16.56 to **16.06 years**, and Spain moves from 4th of 6 to
**3rd of 5** — the median of the smaller sample. Germany (29.35) and Croatia (21.31)
stay above Spain; Lithuania (15.34) and Finland (13.41) stay below. So the robust
claim is "Spain is not the most expensive relative to rent"; "lower half" is a
property of the six-country sample, not of the measure. Both are now stated.

---

## D25. Report the mixed endpoint, and check the 2025-only median

**Context.** The OECD series end in 2025 for most countries but not all: Israel
stops in 2016, Iceland and Russia in 2019, Colombia in 2024. A "2015→2025" label
would silently misdescribe four countries.

**Decision.** Call the window **2015→latest**, store the endpoint of every country,
and report the median restricted to the 2025 endpoint as a sensitivity
(`endpoint_sensitivity` in `results.json`).

**Why.** Using every country maximises coverage, but the benchmark then mixes
endpoints. Restricting to 2025 is cleaner but drops four countries. Reporting both
costs one paragraph and removes the ambiguity: the price-to-income median is +9.3%
on 40 countries and **+10.6% on the 36 that reach 2025**; Spain is 7th in both.

**Alternatives rejected.**

- *Relabel the window 2015→2025 and ignore the four short series.* It would be
  false for Israel, Iceland, Russia and Colombia.
- *Use only the 36 countries with a 2025 endpoint.* It is defensible, but it throws
  away coverage for a benchmark that barely moves, and the 2000 window already has
  a smaller sample.

**Consequence.** The README table header says "2015→latest", the per-country
endpoint is in `comparative_countries.csv`, and the 2025-only median is a stored
number, not a footnote computed by hand.
