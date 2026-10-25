# RED_TEAM.md — attacking the project before someone else does

Written as if I were a referee hostile to the result. Each objection, then what
the project does about it, then what remains unresolved.

---

## "Your null is just a bad measure."

**Fair.** `share_nonurbanizable` is a share of municipal area and correlates with
rurality. The project says so and shows the raw-vs-adjusted figure precisely to
demonstrate the artefact.

**But** the critique cuts both ways: the same coarseness would bias *towards*
finding an effect if any existed in the direction of the hypothesis, because
restricted municipalities are systematically expensive coastal/urban ones. The
observed sign is the opposite, so measurement error alone does not explain it
away. The honest conclusion is "not identified", not "no effect".

**Unresolved:** a parcel-level or capacity-weighted measure would be better. Not
available in a reproducible public form.

---

## "Your null is just one rent series."

**It was, and now it is two.** The first version used only INE table 69330. The
project now repeats the same five specifications with SERPAVI, a tax-based rent
series built from *Modelo 100* declarations. The two correlate at 0.991 in levels,
and annualised the median ratio is 0.959 — different statistics, same places.

The tax-based coefficients are essentially the INE ones: pending share −2.4%
(p=0.003), unstarted share −2.2% (p=0.031), non-urbanizable −4.0% (p=0.27),
development land +1.1% (p=0.57). The null is not an artefact of who produced the
rent series.

**What this does not answer:** both series measure the existing rental stock, not
the rent of new build. Two smoothed stock measures agreeing is not evidence about
the margin the hypothesis is really about. And SERPAVI is narrower: collective
residential buildings only, no Navarra or Basque Country, censored small cells.

**Unresolved:** a new-build rent series at municipal level, or a repeat-sales /
new-tenancy index. Neither is available here.

---

## "You added controls until the result disappeared."

**Partially fair, and worth confronting directly.**

The controls were specified by the confound, not by the result: density and
consolidated-urban share are the obvious determinants of both land
classification and rents. They were chosen before the adjusted run, and the basic
vs urban pair is shown side by side in figure 3 rather than only the version that
supports the story.

**However:** the choice to *report* the urban-control version as the headline is
a judgement. A reader who prefers the basic specification sees −0.10, p < 0.001,
still the wrong sign. So the conclusion is robust to that choice, which is the
real defence.

---

## "With 431 municipalities and 52 clusters you cannot distinguish 0 from −0.05."

**Correct.** The confidence interval on non-urbanizable share is roughly
[−0.12, +0.03]. The project does not claim the coefficient is zero. It claims the
predicted negative effect is not detectable, and the point estimate is small and
of the wrong sign.

The two coefficients that are significant (pending share, unstarted share) are
reported but not treated as discoveries: they are 2 of 20 specifications and
would not survive a Bonferroni correction.

---

## "The pipeline gap could just be the 2008 crash."

**Plausible and not excluded.** Much of the planned stock was drawn up before
2007; the crash stopped construction; the SIU snapshot in the 2020s still counts
it as pending.

**What the project can say:** the gap is not cleared by demand. Fast-growing
municipalities still have 71% pending. That weakens, but does not eliminate, the
"it is all legacy 2007 stock" explanation — a fast-growing municipality could
still be sitting on 2007 paper.

**What would settle it:** plan dates per sector, which the SIU does not provide
in a comparable form.

---

## "You are implying hoarding without evidence."

The README explicitly separates "not built" from "retained strategically". The
word "hoarding" does not appear as a finding. The interpretation section lists
financing, infrastructure, land assembly and phasing as candidate mechanisms and
says the data cannot distinguish them.

**Residual risk:** a reader skimming the charts may still infer speculation. The
figure titles are descriptive ("Where the paper housing is concentrated"), not
accusatory.

---

## "Municipal average rent is the wrong outcome."

**Correct, and stated.** The hypothesis is about the marginal new unit; the data
measure the average of the stock. This attenuates any true effect towards zero.
It is one of the reasons the null is not strong evidence against the hypothesis.

---

## "You dropped the 2025 observations to make the sample look complete."

The panel keeps 2025. Rent regressions drop those rows because rent is missing,
not by an explicit filter. `coverage.json` reports both the panel span and the
non-missing counts per variable. A reader can reconstruct exactly which rows each
model used via `n` in `results.json`.

---

## "The 5.17 million figure is a national total presented as if it were the universe."

It is not presented that way. Every mention is scoped to the 431 municipalities.
The SIU has 5,898 municipalities and its national aggregate would be larger;
the README calls the figure a lower bound on plan capacity in the sample.

---

## "Why no instrumental variable? Saiz (2010) did it with terrain."

Because a credible instrument needs terrain data at municipal level, and Spanish
municipal boundaries make the Saiz approach harder: many municipalities are
enormous and include both mountains and plains, so a municipal terrain index has
little within-unit meaning. Assembling it was out of scope for this iteration.

**If I had another week:** Copernicus DEM + municipal boundaries, compute the
share of land above a slope threshold, use it as an instrument for development
capacity, and be explicit that the exclusion restriction (terrain affects rents
only through land supply) is strong and probably violated by amenities.

---

## "The panel interaction is fragile."

**Yes.** Non-urbanizable × growth is −0.10 with year FE and −0.17 with
province-year FE; planned capacity × growth is −0.10 with year FE but −0.03
(p = 0.24) with province-year FE. The result depends on how regional shocks are
absorbed, which is a warning sign, and the README says so.

The panel is included because it is the best available check on the
cross-section, not because it identifies a supply elasticity.

---

## "This is a null result dressed up as a project."

**The strongest objection, and the one the project tries hardest to answer.**

The defence: the project has a large, directly measured, non-obvious descriptive
finding (3.49 million unbuilt planned dwellings, 48.8% of development land not
started, and a gap that demand growth does not close) *plus* a well-documented
failed identification attempt. The failed attempt is informative because the
naive result is so strong and so misleading, and showing why is useful to anyone
who works with municipal land data.

If a reader wants a positive causal headline, this is not the project. That is a
feature.

---

## "You chose the countries to make Spain look bad."

**No: the country sample is the full OECD price-to-income set (40 countries), the
full European permit set that passes a coverage rule (34 and 33), and every
comparable Urban Audit city in the six countries with rent data.** There is no
hand-picked peer group in the headline. The bar chart shows 16 peers because 40
bars do not fit, but the rank and the median are computed on all 40.

The result is also not uniformly unflattering: Spain is **7th of 40**, not 1st,
and its city price-to-rent is **4th of 6** — in the lower half. A cherry-picked
sample designed to make Spain look bad would not report that.

**Unresolved:** the 16-peer bar is a presentational choice. A reader who wants the
full distribution should use `comparative_countries.csv`.

---

## "House price indices are not comparable across countries."

**Correct, and the chapter only compares changes.** The OECD series are indices
with different national sources and quality adjustment. Comparing 2015→latest
changes removes the level problem but not the construction problem. The project
says so in `LIMITATIONS.md` §11.1 and never compares price-to-income levels across
countries.

**What would fix it:** a harmonised repeat-sales or hedonic index with common
quality controls. That does not exist for this country set.

---

## "Permits are not completions. You are measuring paperwork again."

**Fair.** Permits lead construction and can be delayed or abandoned. The chapter
uses them because they are the only annual, country-comparable flow measure. It
does not call them completions, and it does not use them to estimate the Spanish
pipeline. The Spanish pipeline is measured separately from SIU planned and pending
dwellings.

The permit gap is large enough that the objection does not rescue the comparison:
Spain is at 2.64 per 1,000 against a median of 4.62, and at 16% of its own 2006
permit peak. Even a large permits-to-completions wedge would leave Spain low.

**Unresolved:** a harmonised completions series would be better. Eurostat's
completions data are less complete and less comparable than permits.

---

## "Your city result contradicts your story. Spanish cities are cheap relative to rent."

**It does, and the chapter reports it rather than hiding it.** Spain's median city
price-to-rent is 16.56 years, 4th of 6 on a 1 = highest rank; German cities are at
29.48. That means Spanish cities are **not** the most expensive in this sample
relative to rent. It is consistent with a rental-market squeeze (rents high
relative to prices) rather than a purchase-price bubble.

The chapter's claims are therefore narrower than "Spain is the most expensive
country": Spain had **high price growth** and **low permitting**, and its cities
are **mid-to-low on price-to-rent**. Those are different margins, and the chapter
keeps them separate.

**Unresolved:** six countries is a thin city sample, the years differ, and the rent
measure is an average for the city, not a new-tenancy rent.

---

## "The rent-unit rule is a hack."

**It is a heuristic, and it is documented.** Eurostat labels the rent indicator
"average annual rent per m²", but the German and Portuguese values are about 8.5
EUR/m² — plainly monthly — while the Spanish, Finnish, Croatian and Lithuanian
values are above 82. The label cannot be trusted, so the rule uses the magnitude:
country median raw rents separate into a monthly group around 8.5 EUR/m² and an
annual group at 41 EUR/m² or more, and the 20 threshold is not near any country's
values. The rule is applied per country because reporting units are a national
convention. Latvia is excluded because its four cities are internally inconsistent
under any single unit.

A reader who dislikes the rule can redo it: `comparative_cities.csv` carries the
raw rent, the inferred unit and the comparability flag. The conclusion about
Spanish cities is not driven by a marginal case; the gap to Germany is 13 years.

**Unresolved:** the rule could misclassify a country whose rents cluster near 20
EUR/m². None does in this sample.

---

## "You compare Spanish cities in 2023 with German cities in 2022."

**Yes, and a common year is impossible without dropping Spain or Germany.** The
Urban Audit rent and price series do not share a common latest year across the six
countries. The year is reported for every city, and each ratio uses price and rent
from the same city and year, so the mismatch is across countries, not inside a
ratio.

**Unresolved:** a common-year comparison would be cleaner. It would also cut the
sample to the countries that happen to publish the same year, which is a different
selection problem.

---

## "Spain is 17% below its 2007 price-to-income peak, so there is no housing problem."

**That is one of the three peak comparisons, not the whole picture.** Price-to-rent
is **1.9% below** its 2007 peak and real prices are **12.8% below**. The ratios
disagree because their denominators moved differently. The project reports all
three and does not treat the 2007 peak as a normative benchmark. Being below the
peak is not the same as being affordable, and the 45.7-year pipeline is a separate
measure.

The chapter explicitly does **not** decompose price-to-income into rents and
incomes: the OECD rent index is a national deflator, not the municipal market rent
series used in the Spanish core.

---

## "You still have not dimensioned the 45.7-year pipeline."

**Correct, and no cross-country measure exists.** The chapter dimensions the flow
(permits) and the price outcome, not the stock of planned-but-unbuilt dwellings.
That is why the synthesis table's two pipeline rows carry
`benchmark = "No comparable cross-country measure"` rather than a fake comparison.

The honest claim is: Spain permits less than most European peers and its pipeline
is equivalent to decades of recent construction. The chapter supports the first
half with a distribution and the second half with the Spanish data. It does not
claim that Spain's pipeline is the largest in Europe.

**Unresolved:** a harmonised cross-country measure of permitted-but-unbuilt
dwellings would require construction and permit data linked at the project level.
No public source does that across countries.

---

## "Your city layer mixes cities with greater-city areas."

**Yes, and it is stated rather than hidden.** Eurostat publishes some units on
municipal boundaries and some as "greater city" aggregates: 44 of 251 comparable
cities, including Madrid, Barcelona, Valencia, 25 of 87 Spanish cities and all 16
Portuguese ones. The ratio is internally consistent because price and rent come
from the same geography, but the absolute city medians mix two spatial definitions.

**Why not drop them.** Dropping greater-city units would remove every Portuguese
city, Madrid, Barcelona and Valencia — most of the large Spanish cities and one of
the six comparison countries. That is a worse sample, not a cleaner one.

**Unresolved:** there is no public crosswalk that would convert the greater-city
indicators to municipal boundaries. The `city_name` column keeps the suffix, so a
reader who wants strict municipal comparability can filter to `not contains
"(greater city)"` and accept a much smaller, smaller-city sample.

---

## "Why not regress prices on permits across countries?"

Because it would be a spurious correlation generator. Permits, prices, credit,
migration and construction capacity are jointly determined; countries differ in
measurement; and country fixed effects would absorb the permit measure. With 33–40
cross-sectional observations and no credible instrument, a coefficient would look
precise and mean nothing.

The chapter's job is to place Spain in a distribution, not to estimate a
cross-country elasticity. The Spanish core already has a within-country design,
and even that is explicitly non-causal.
