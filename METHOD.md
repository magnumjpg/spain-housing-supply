# METHOD.md — what is estimated, and why

The project has four layers: a descriptive inventory, a stock-over-flow absorption
ratio, a cross-section, and a short panel. They answer different questions and are
not substitutes.

---

## 1. The descriptive layer: how big is the gap?

No model. Direct arithmetic on the matched cross-section of 431 municipalities.

```
planned_to_stock   = Σ planned_dwellings / Σ stock_catastro
pending_to_stock   = Σ pending_dwellings / Σ stock_catastro
pending_share      = Σ pending_dwellings / Σ planned_dwellings
unstarted_share    = (area-weighted) Σ dev_area × munpradsnu / Σ dev_area
```

Aggregates are computed on sums, not as averages of municipal ratios, because a
municipality with 300 planned dwellings should not count as much as Madrid with
243,909. Medians are reported alongside, because the distribution is skewed and
the two answer different questions ("how much housing" vs "how typical is a
municipality").

### 1b. Years of pending supply

The stock-over-flow ratio translates the pipeline into time:

```
years_to_absorb_i = pending_dwellings_i / ((stock_2025_i - stock_2023_i) / 2)
```

The denominator is the **net** annual change in the Catastro conventional-dwelling
stock. Net additions subtract demolitions, so the ratio is an **upper bound** on
the years of gross construction the pipeline represents. It is computed only for
municipalities with non-missing stock in both years and positive net additions
(359 of 431). The aggregate is `Σ pending / Σ net additions`, not the average of
municipal ratios.

The 2023–2025 window is the headline because Catastro stock coverage expands
sharply in 2023 (119 municipalities before, 399 after). Using a longer window
would restrict the sample to the large cities that were covered earlier and would
confound the ratio with sample selection. The 2021–2025 window is reported on those
115 municipalities as a robustness check: 34.8 years versus 45.7, same order of
magnitude.

This is a description, not a projection. It does not assume that demand,
construction capacity or plans stay constant.

---

## 2. The cross-section: do land restrictions show up in rents?

### Specification

For municipality *i* in province *p*:

```
log(rent_i) = α_p + β · z(measure_i) + γ' X_i + ε_i
```

- `α_p`: province fixed effects. Absorbs regional price levels, regional
  planning law, coastal status at province level, and any common shock.
- `z(measure)`: each land measure standardised to mean 0, SD 1 **within the
  estimation sample**. β is therefore "the association with a one-standard-
  deviation difference in the measure", which is comparable across measures with
  wildly different units (shares vs dwellings per 1,000).
- Standard errors clustered by province (52 clusters). Municipalities within a
  province share planning regimes and housing markets; ignoring that would
  overstate precision.

### Controls

`BASIC`: log population, log housing stock, log population growth 2015–2024.
`URBAN`: the above plus log population density and the share of consolidated
urban land.

The density and consolidated-urban controls matter. Without them, the
non-urbanizable share is essentially a rurality index and the coefficient is
large and negative for reasons unrelated to planning. Adding them is not
cosmetic: it is the difference between the headline −0.55 raw correlation and
the −0.05 adjusted coefficient.

### Outcomes

Three, because they triangulate:

| Outcome | Why |
|---|---|
| `log(rent_m2_year)` | The affordability margin the hypothesis is about |
| `log(price_m2)` | Owner-occupier market, a check that the rent result is not a rental-specific artefact |
| `log(rent/price)` | Gross yield. If land restriction raises prices but not rents, yield falls |

### Measures

| Measure | Definition | What it proxies |
|---|---|---|
| `share_nonurbanizable` | `MunPrSnUzb / 100` | Land restriction at the municipal boundary |
| `share_development_areas` | `MunPrADes / 100` | Land designated for growth |
| `planned_per_1000_stock` | `munnumviv / stock × 1000` | Plan capacity relative to the built stock |
| `pending_share` | `munnvivpnd / munnumviv` | How much of the plan is unbuilt |
| `unstarted_share` | `munpradsnu / 100` | How much development land has not begun urbanisation |

`plan_age` (2025 − plan year) is used only as a robustness control, not as a
headline measure, because the plan year is inconsistently recorded across
regions.

### Independent outcome check: SERPAVI

The same five specifications are re-estimated with `log(rent_m2_serpavi)` as the
outcome, where `rent_m2_serpavi` is the 2024 SERPAVI median monthly rent per m²
from *Modelo 100* tax records. This is not a robustness variant of the same data;
it is a different measurement with a different unit and a different sample frame.
It answers one question: **is the rent null an artefact of the INE rent series?**

The specification, controls and clustering are identical, so the two sets of
coefficients are directly comparable as "association per standard deviation".
The comparison is reported in `results.json` under `serpavi`, not pooled with the
INE estimates. No weighting by the number of declarations is applied; the
smallest municipality in the sample still has 30+ declarations, so weighting
would mostly re-weight toward Madrid and Barcelona.

---

## 3. The panel: does growth pass through into rents?

The cross-section cannot separate "restricted places are expensive" from
"expensive places restrict". A panel with municipality fixed effects removes all
time-invariant municipal characteristics, and interacts the land measure with
population growth:

```
log(rent_it) = α_i + δ_t + θ · measure_i × Δlog(pop_it) + φ · Δlog(pop_it) + ε_it
```

`α_i` is municipality FE, `δ_t` is year FE (or province × year FE). The
coefficient of interest is θ: **does a given population increase raise rents
less where land capacity is higher?**

- If the restriction hypothesis holds, θ < 0 for capacity measures and θ > 0 for
  restriction measures.
- With province × year FE, any region-wide shock (a tourism boom, a regional
  rent law, a national interest-rate cycle) is absorbed. This is the demanding
  version.

The panel runs 2013–2024 on the rent index. The land measure is time-invariant
(the SIU is a snapshot), so its level is absorbed by the municipality FE and only
the interaction is identified. This is deliberate and is stated as a limitation:
the design cannot estimate the effect of a *change* in classification.

---

## 4. Responsiveness: does planning follow demand?

A simple cross-section:

```
planned_per_1000_stock = α_p + β · population_growth_15_24 + γ · log(pop) + ε
```

This is not a causal test. It is a sanity check on the "planners ignore demand"
story. If β > 0, planning does respond to growth at least in direction.

---

## 5. What was tried and discarded

Documented so the null result is not mistaken for a design that was never
attempted.

| Design | Why discarded |
|---|---|
| Raw correlation rent vs non-urbanizable share | Reported, but it is a rurality artefact. Kept only as the "before" panel of figure 4 |
| Instrument with municipal area / topography | No credible terrain measure was assembled within the time budget; municipal area is endogenous to classification |
| Event study around plan approval dates | `plan_mun.xlsx` has 8,132 instruments but the dates are heterogeneous (approval vs update) and not comparable across regions. Not fit for a credible event study |
| Rent-to-income | No municipal household income in the Urban Indicators. The INE ADRH (household income atlas) exists but is a different geography (census tracts/sections) and would need its own crosswalk |
| Monte Carlo / synthetic counterfactual | Rejected. It would manufacture precision the data do not have |
| Welfare / deadweight-loss calculation | Rejected. It requires an elasticity this design cannot identify |

---

## 6. Why the headline is a null

The honest summary of the cross-section is: **after province FE and
urbanisation controls, none of the five land measures has the predicted
negative association with rents, and two are negative and significant.**

That is not "land classification does not matter". It is:

1. The measure is coarse (share of municipal area, not buildable capacity in the
   right place).
2. The treatment is chosen, not assigned.
3. The outcome is municipal average rent, not the rent of new-build units on
   newly classified land.
4. The SIU is a snapshot, so the treatment is measured after much of the outcome.

The project therefore moves the claim to what the data can carry: **a large,
measurable gap between planned and built housing, which is not explained by
demand growth.**

---

## 7. The comparative chapter: benchmarking, not identification

The chapter answers "is Spain unusual?" with distributions, medians and ranks. It
does not estimate a cross-country effect, for a simple reason: permits, prices,
credit, migration and construction capacity are jointly determined, and with 33–40
cross-country observations there is no credible exclusion restriction. A regression
of prices on permits would produce a precise-looking coefficient with no causal
meaning. Country fixed effects would absorb the permit measure entirely. The
chapter therefore stops at description.

### 7.1. Country prices

For country *c* and measure *m* (price-to-income, price-to-rent, real prices):

```
change_2015_c = (I_c,latest / I_c,2015 - 1) × 100
change_2000_c = (I_c,latest / I_c,2000 - 1) × 100
```

`I` is the OECD index with base 2015 = 100. The latest year is country-specific
(2025 for most). The median is taken over the countries with a non-missing change;
the rank is descending (1 = highest change) and is computed **inside the same
sample as the median**.

The own-history peak is separate:

```
latest_vs_peak_c = (I_c,latest / max_t I_c,t - 1) × 100
```

This is not a cross-country benchmark. It exists because a country can be above the
sample median and still below its own peak, and the reader needs both facts. The peak
year is stored, so the 2007 anchor can be checked.

Real house prices are ranked inside the 40-country price-to-income sample, not the
47-country real-price-only set. This keeps the four price rows on one country
universe; the 47-country set is a superset that includes partner economies.

The latest year is country-specific, so the median is computed over the endpoints
each country actually has. To show what that costs, the project also computes the
median restricted to the countries whose series reach the full endpoint (2025):
that is `endpoint_sensitivity` in `results.json`. For price-to-income it moves the
median from +9.3% (40 countries) to +10.6% (36 countries) without changing Spain's
rank. The chapter reports the mixed-endpoint median as the headline because it uses
every country, and the restricted median as the check.

### 7.2. Country supply

```
permits_per_1000_c,t = permits_ths_c,t × 1,000,000 / population_c,t
window_mean_c,w = mean(permits_per_1000_c,t for t in window w)
```

A country-year is used only when both the permit count and the population are
observed. A window mean requires at least three annual observations. The windows
are 2015–2019 and 2021–2024; 2025 is excluded because it is preliminary.

The denominator is population, not households or the dwelling stock, because
annual household counts are not on the same country panel. This is a deliberate
compromise and is listed as a limitation.

### 7.3. City price-to-rent

For city *i* in country *c*, latest year *t*:

```
price_to_rent_i = price_m2_i,t / rent_m2_annual_i,t
```

`rent_m2_annual` is the Urban Audit rent after the country-level unit rule:
multiply by 12 if the country median raw rent is below 20 EUR/m², otherwise leave
as annual. Latvia is excluded because its four cities are internally inconsistent
under any single unit.

The country median is the median of city ratios, not a ratio of medians. The
country median is then ranked across the six countries. Spain's rank is therefore
a rank among six country medians, not among 87 Spanish cities; the summary table
stores `rank_n = 6` and `n = 87` separately.

The city is whatever geography Urban Audit publishes: a municipal boundary or a
"greater city" aggregate. Both are kept, because dropping greater-city rows would
remove Madrid, Barcelona, Valencia and every Portuguese city. Each ratio uses price
and rent from the same geography, so the ratio is internally consistent; the
country medians mix the two spatial definitions, which is stated as a limitation.

The same function computes the municipal-boundary-only sensitivity, so the reader
does not have to take the mix on trust: dropping greater-city units leaves 207
cities in five countries, Spain's median falls to 16.06 years and its rank is 3rd
of 5. See `city_layer.municipal_only_sensitivity` in `results.json`.

The city measure is a gross yield in years. It is **not** rent-to-income, and a
low value can mean cheap housing or expensive rents.

### 7.4. The synthesis table

`comparative_summary.csv` has nine rows: six country metrics, one city metric, and
two rows that bridge back to the Spanish pipeline (pending years and pending
dwellings). The two pipeline rows carry `benchmark = "No comparable cross-country
measure"` and a null rank, because no harmonised cross-country pipeline measure was
found. They are in the table to connect the chapter to the core, not to claim a
comparison.

### 7.5. What was deliberately not done

| Design | Why not |
|---|---|
| Cross-country regression of prices on permits | No credible identification; joint determination; country FE would absorb the measure |
| Comparison of price-to-income **levels** | OECD publishes indices, not levels; national definitions differ |
| City price-to-income | Urban Audit income stops in 2019/2020; numerator and denominator would be five years apart |
| Combining OECD price-to-rent with municipal rents | The OECD rent index is a national deflator, not the market rent series; dividing the two indices would be a false decomposition |
| Comparing the 45.7-year pipeline across countries | No harmonised "planned but unbuilt" measure exists |
| A regulation index | Different concept, different year, invites a causal reading the design cannot support |
