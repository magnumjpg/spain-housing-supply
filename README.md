# Permission Without Construction

**Land classification, unbuilt plan capacity, and rental costs in Spain**

*The working title was "The Permission Premium". The data did not support a premium. They supported a gap.*

---

## The finding

Spain's urban planning system gives municipalities the power to decide which land can be built on. The standard critique is that this power restricts the supply of land and pushes up rents. I tested that link with official data.

**The rent test does not confirm it.** The rent section below explains exactly why, and the reason is informative rather than mysterious: a single municipal cross-section cannot separate land classification from the urban–rural gradient, and land classification is chosen by the municipality. That is a limit of this design, not evidence that planning does not matter.

But the same data show something larger, more concrete and fully measurable: **3.49 million dwellings have planning permission and have not been built.** At the 2023–2025 rate of net housing additions, that pending stock is equivalent to **45.7 years of construction** in the 359 municipalities where the housing stock is observed in both years. The median municipality has **48 years** of pending supply; **76%** have more than 20 years.

That is the project. The pipeline is not a rounding error or a handful of stalled projects. It is decades of housing that exists on paper and not on the ground.

## The rent question, in one paragraph

Do municipalities that classify more land have lower rents? **Not in this sample, once province and urbanisation are held constant.** The raw correlation is −0.55, but that is mostly because the non-urbanizable share is a rurality index: rural places have cheap rents for reasons unrelated to planning. With urban controls, the association is a null. The two coefficients that are statistically distinguishable from zero are negative — more unbuilt capacity goes with *lower* rents — which is consistent with planning following demand rather than constraining it. I also repeat the test with SERPAVI, an independent tax-based rent series, and get the same answer. None of this identifies a causal effect; see the rent section below and `LIMITATIONS.md`.

## What I built

A municipal dataset that, as far as I can tell, did not exist as a single reproducible table:

- **Land classification**: the MIVAU *Sistema de Información Urbana* (SIU), 5,898 municipalities, with the share of municipal land in each class, the surface of development areas, planned dwellings, and dwellings still pending.
- **Outcomes**: INE *Indicadores Urbanos* (table 69330), 434 municipalities, 2010–2025, with annual rent €/m², mean and median rent, house prices, housing stock, vacancy, households and household size. A second outcome series, MIVAU **SERPAVI** (tax records, 2024), is used as an independent check on the rent result.
- **Demand controls**: INE Padrón (table 29005), municipal population 1996–2025.

The sources are merged on the 5-digit INE municipal code. The SIU match is 431 of 434 urban municipalities; all 431 have a SERPAVI rent. Every number below comes from `src/run_all.py` and is stored in `outputs/results.json`.

## The headline numbers

| | |
|---|---|
| Urban municipalities in the matched sample | **431** |
| Dwellings planned in development areas | **5.17 million** |
| Planned dwellings not yet materialised | **3.49 million (67.5%)** |
| Pending pipeline at the 2023–2025 construction rate | **45.7 years** (359 municipalities) |
| Median municipality's years of pending supply | **48.3 years** |
| Municipalities with more than 20 years of pending supply | **76.0%** |
| Median municipality's pending share | **72.1%** |
| Planned capacity relative to existing housing stock | **33.4%** |
| Development land that has not started urbanisation | **48.8%** (area-weighted) |
| Municipalities where more than 80% of planned dwellings are pending | **35.7%** |

The 5.17 million planned dwellings sit in 256,606 hectares of development land. If every pending dwelling were built, the housing stock of these 431 municipalities would grow by about a third. Two-thirds of the pipeline has not been materialised.

This is not a rural artefact. Madrid alone has 158,113 pending dwellings; Murcia 111,116; Toledo 88,698. Toledo's plan envisages more than twice the city's existing stock.

### How long is the pipeline?

The stock-over-flow ratio is the number that makes the gap interpretable. For each municipality with Catastro stock observed in both 2023 and 2025, I divide pending dwellings by the average annual net change in the conventional-dwelling stock. Across 359 municipalities:

- **3.17 million** pending dwellings;
- **69,411** net additional dwellings per year;
- **45.7 years** of pending supply at that rate;
- median municipality **48.3 years** (p25 20.9, p75 136.3);
- **76.0%** of municipalities above 20 years, **49.6%** above 50 years.

The 2021–2025 window, on the 115 municipalities with continuous stock coverage over the longer period, gives **34.8 years**. The order of magnitude is robust to the window: decades, not years.

Two caveats are built into the number. The denominator is *net* additions, which subtract demolitions, so it understates gross construction and the ratio is an **upper bound**. And pending is a stock, not a committed flow: some of it may never be built. The claim is not "Spain will exhaust this in 46 years"; it is "at recent construction rates, the pipeline is equivalent to four decades of supply". That is enough to reframe the policy question from "how much land is classified" to "why the classified capacity is not being converted".

### External check

MIVAU publishes its own national aggregate for the same source. Across **5,900 reporting municipalities** it counts **9.60 million planned dwellings and 7.09 million pending**, a pending share of **73.9%**, with **55.9%** of development land not started.

The 431 municipalities analysed here account for **53.8% of that national planned capacity** and 49.2% of the pending stock. So this is not a niche sample, and it is not a different universe: the national pipeline is, if anything, slightly *more* unbuilt than the urban one. The 5.17 million figure is a subset of the 9.60 million, not a competing estimate.

## The rent test: what it can and cannot show

Read this section as a failed identification, not as the project's main result. It is here because the hypothesis was stated first and the null is part of the answer.

### 1. The raw correlation runs the wrong way

Municipalities with a larger share of non-urbanizable land have **lower** rents, not higher: the raw correlation with log rent is **−0.55**. Municipalities with more development land have higher rents (**+0.30**). That is the opposite of the restriction hypothesis.

It is also almost certainly not a treatment effect. Non-urbanizable share is close to a measure of "how rural is the municipality". Rural places have cheap rents for reasons that have nothing to do with planning.

### 2. Once urbanisation is held constant, the association disappears

Adding province fixed effects and controls for population, housing stock, population growth, density and the share of consolidated urban land:

| Measure (per 1 SD) | Association with log rent | p-value |
|---|---:|---:|
| Share of non-urbanizable land | −4.6% | 0.21 |
| Share of development land | +1.5% | 0.45 |
| Planned dwellings per 1,000 existing | +3.9% | 0.09 |
| Share of planned dwellings pending | −2.3% | 0.008 |
| Share of development land not started | −2.3% | 0.026 |

None of the coefficients has the sign the restriction hypothesis predicts (positive for restricted land, negative for development capacity). The two that are statistically distinguishable from zero are negative: **more unbuilt capacity is associated with lower rents**, which is what you would expect if planning follows demand rather than constraining it.

The same pattern holds for prices: the signs are identical and nothing is significant (non-urbanizable −8.4%, p = 0.21; development land +5.1%, p = 0.15). The gross yield tells a different story — development land is associated with a 3.4% lower rent-to-price ratio (p = 0.04) — which is what you would expect if prices respond more strongly than rents, not if rents alone were being held up. Figure 4 shows the mechanism for rents: the raw slope is steep, and after province and urbanisation controls the binned relationship is flat.

### 2b. A second, independent rent series says the same thing

INE table 69330 is one measurement of rents. To check that the null is not an artefact of that series, I repeated the cross-section with **SERPAVI**, MIVAU's rent index built from *Modelo 100* income-tax declarations. It is a different operation, a different unit (median monthly rent per m² of collective residential buildings, not mean annual rent per m²), and a different sample frame.

All **431** municipalities have a SERPAVI rent. **406** also have an INE rent. The two agree closely in levels — Pearson **0.991** (0.992 in logs) — and annualised, the median SERPAVI/INE ratio is **0.959** (p10–p90: 0.916–0.997), which is what a median-versus-mean comparison should look like. Agreement is a cross-source check, not a restatement: the series are not the same measurement.

With the same urbanisation controls and province fixed effects, the tax-based series reproduces the INE result almost coefficient for coefficient:

| Measure (per 1 SD) | SERPAVI rent | p-value | INE rent (for comparison) |
|---|---:|---:|---:|
| Share of non-urbanizable land | −4.0% | 0.27 | −4.6% |
| Share of development land | +1.1% | 0.57 | +1.5% |
| Planned dwellings per 1,000 existing | +3.5% | 0.15 | +3.9% |
| Share of planned dwellings pending | −2.4% | 0.003 | −2.3% |
| Share of development land not started | −2.2% | 0.031 | −2.3% |

The two variables that are distinguishable from zero remain negative. The restriction hypothesis does not reappear when rents are measured from tax records.

SERPAVI has its own limits: it excludes Navarra and the Basque Country (foral tax regimes), it is censored where the number of declarations is too small to publish, and its definition — collective residential buildings — drops part of the rental stock. Those limits are why it is a robustness check next to INE, not a replacement.

### 3. The panel does not rescue the hypothesis

I also estimated whether population growth passes through into rents more strongly where land is restricted, with municipality fixed effects and either year or province-year fixed effects. The interaction is never positive and significant:

- Non-urbanizable share × population growth: **−0.17** with province-year FE (p = 0.004).
- Planned capacity × population growth: **−0.10** with year FE (p = 0.003), but **−0.03** (p = 0.24) once province-year shocks are absorbed.
- Pending share × population growth: indistinguishable from zero.

A negative interaction is consistent with supply responding where capacity exists, but it is fragile to regional shocks. I do not claim it as a supply-elasticity estimate.

### 4. Demand growth does not close the gap

Fast-growing municipalities do plan more: the top tercile of population growth has a median of 375 planned dwellings per 1,000 existing, against 309 in declining municipalities. But the pending share barely moves: **71.3%** in fast-growing places versus **75.1%** in declining ones. The pipeline is not a rural curiosity that demand would clear.

### 5. A competing explanation: plan vintage

There is a simpler reason why some places show a large pending stock. The SIU records the approval year of each municipality's general plan, and newer plans have had less time to be built out.

Median pending share falls monotonically with plan age: **85%** where the plan is five years old or less, **66%** where it is 21–30 years old, **58%** where it is more than 30 years old. The correlation between plan age and pending share is **−0.36**.

This is not a nuisance to be controlled away. It is a direct warning against reading the 3.49 million pending dwellings as obstruction: a municipality that approved a large expansion in 2022 *should* have almost all of it pending.

The counter-argument is that the aggregate is dominated by older plans. It is: **74% of the pending dwellings sit under plans approved more than 15 years ago**, and even the oldest plans still have 58% pending. So plan vintage explains part of the cross-sectional variation — and is reported rather than hidden — but it does not reduce the gap to a story about recent plans that have not had time to build.

## Interpretation

The Spanish planning system produces a lot of **paper housing**: land classified, sectors drawn, dwellings counted, and a large share of it never converted into buildings. The observable bottleneck in these data is not the headline stock of classified land. It is the step between permission and construction.

That reframes the policy question. If the debate is about how much land is classified as urbanizable, the data suggest the debate is aimed at the wrong margin. The margin that shows up is execution: land assembly, infrastructure, financing, the sequencing of plan approval, and the incentives of landowners to build rather than hold. The data cannot tell us which of these dominates. They can tell us that the classification share is not a good proxy for the constraint.

It also explains why the naive cross-section is so misleading. Land classification is not assigned to municipalities; it is chosen by them, in response to demand, geography and politics. A municipality that expects to grow classifies land. A municipality that is rural, protected or shrinking does not. Regressing rents on that choice without a source of exogenous variation mostly recovers the urban–rural gradient.

## What this does not prove

- **No causal effect of land classification on rents.** The design is cross-sectional and the treatment is endogenous. The null is not evidence that classification does not matter; it is evidence that this design cannot detect it.
- **The 45.7-year ratio is a description, not a forecast.** It divides a stock by a recent net flow. Demolitions are subtracted in the denominator, so it is an upper bound; demand can grow, plans can be revised, and part of the pending stock may never be built. It says "decades at recent rates", not "exhausted in 2050".
- **No corruption claim.** Nothing here measures corruption, influence or wrongdoing. The gap between planned and built housing is consistent with many explanations, including the 2008 crash, slow infrastructure, financing constraints and rational landowners.
- **The pending variable is a stock, not a delay.** `munnvivpnd` counts dwellings planned in development areas that have not been materialised at the date of the SIU image. It does not say when they were planned, or whether they were ever expected to be built soon.
- **The SIU is a snapshot.** Land classification is measured around 2020–2025, while rents run to 2024. Any panel design using this measure is compromised by the fact that the "treatment" is observed after part of the outcome.
- **The sample is urban.** 431 municipalities, not all 8,000. They are the INE urban-indicator municipalities, and they hold 15.5 million dwellings.
- **SERPAVI is a different, narrower measurement.** It covers collective residential buildings from tax records, excludes Navarra and the Basque Country, and censors small cells. It is used as an independent check on the INE rent null, not as a second estimate to average with the first.
- **Rent is not affordability.** I do not observe municipal household income, so I cannot compute rent-to-income. The outcome is rent per square metre.

## Reproduce

```bash
python -m pip install -r requirements.txt
python src/run_all.py
python -m pytest tests -q
```

`run_all.py` downloads the raw files into `data/raw/` (about 120 MB, cached),
builds the panel, estimates the models, writes `outputs/results.json`, and
redraws the figures. The pipeline works offline after the first run.

## Files

```
src/config.py          paths, indicators, province codes
src/download_data.py   downloads + sha256 manifest
src/build_panel.py     parses INE, maps codes, builds panel and cross-section
src/analysis.py        descriptives, regressions, results.json
src/figures.py         seven figures
src/run_all.py         one command
tests/test_pipeline.py invariants
outputs/results.json   every number in this README
outputs/figures/       figures
```

Process documentation, in the order a sceptical reader should read it:

| File | Contents |
|---|---|
| `DATA.md` | Sources, exact variable semantics, the `MunPrADes` double-counting trap, the code crosswalk |
| `METHOD.md` | Specifications, controls, what was tried and discarded |
| `LIMITATIONS.md` | Ten threats, ordered by how much damage they do |
| `DECISIONS.md` | Every choice, including the reframing after the hypothesis failed |
| `RED_TEAM.md` | The objections a hostile referee would raise, answered honestly |
| `ANALYSIS_LOG.md` | Chronological record of what broke and what changed |

## Figures

1. **The unbuilt pipeline** — distribution of pending share and planned capacity by province.
2. **Planned capacity vs demand growth** — the weak responsiveness of planning.
3. **Rent associations** — coefficient plot, basic vs urban controls.
4. **Raw vs adjusted** — why the naive correlation is an urban–rural artefact.
5. **Where the paper housing is** — the 15 municipalities with the largest pending stock.
6. **Growth terciles** — planning responds, the gap does not.
7. **Plan vintage** — newer plans have more pending capacity, which is why the gap is not automatically obstruction.

---

## Resumen en español

El sistema urbanístico español permite a los municipios decidir qué suelo se puede construir. La crítica habitual es que esa discrecionalidad restringe la oferta y encarece el alquiler. El proyecto comprueba que **esa relación no aparece** una vez se compara dentro de la provincia y se controla el grado de urbanización. La correlación bruta va en sentido contrario porque el porcentaje de suelo no urbanizable es, sobre todo, una medida de ruralidad.

Lo que sí aparece —y es el hallazgo principal— es un problema distinto, grande y medible: **5,17 millones de viviendas están planificadas en áreas de desarrollo y 3,49 millones (67,5%) no se han materializado**. Al ritmo de construcción neta de 2023–2025, ese stock pendiente equivale a **45,7 años de obra** en los 359 municipios con stock catastral observado; el municipio mediano tiene **48,3 años** de vivienda pendiente y el 76% supera los 20 años. El 48,8% del suelo de desarrollo ni siquiera ha iniciado la urbanización. En los municipios que más crecen, el 71,3% de la vivienda planificada sigue pendiente, frente al 75,1% en los que decrecen. El cuello de botella observable no es la cantidad de suelo clasificado, sino el paso entre el permiso y la construcción.

El proyecto no afirma causalidad, no mide corrupción y no dice que la clasificación del suelo sea irrelevante. Dice que un corte transversal municipal no permite identificarlo, y que el debate público está mirando el margen equivocado. El resultado se repite con una fuente de alquileres independiente, el SERPAVI de MIVAU construido a partir de declaraciones fiscales (correlación 0,991 con el INE; pendiente −2,4%, p=0,003).
