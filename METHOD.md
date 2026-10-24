# METHOD.md — what is estimated, and why

The project has three layers: a descriptive inventory, a cross-section, and a
short panel. They answer different questions and are not substitutes.

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
