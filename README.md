# Permission Without Construction

**Land classification, unbuilt plan capacity, and rental costs in Spain**

*The working title was "The Permission Premium". The data did not support a premium. They supported a gap.*

---

## The question

Spain's urban planning system gives municipalities the power to decide which land can be built on. The standard critique is that this power restricts the supply of land, pushes up rents, and rewards discretion. I wanted to test the first link with official data: **do municipalities that classify more land for development have lower rents?**

The answer, in this dataset, is no. Not because the opposite is true, but because the cross-section cannot separate land classification from the urban–rural gradient. What the data do show is a different and more concrete problem: **a very large stock of housing that has planning permission on paper and has not been built.**

## What I built

A municipal dataset that, as far as I can tell, did not exist as a single reproducible table:

- **Land classification**: the MIVAU *Sistema de Información Urbana* (SIU), 5,898 municipalities, with the share of municipal land in each class, the surface of development areas, planned dwellings, and dwellings still pending.
- **Outcomes**: INE *Indicadores Urbanos* (table 69330), 434 municipalities, 2010–2025, with annual rent €/m², mean and median rent, house prices, housing stock, vacancy, households and household size.
- **Demand controls**: INE Padrón (table 29005), municipal population 1996–2025.

The two sources are merged on the 5-digit INE municipal code. The match is 431 of 434 urban municipalities. Every number below comes from `src/run_all.py` and is stored in `outputs/results.json`.

## The headline numbers

| | |
|---|---|
| Urban municipalities in the matched sample | **431** |
| Dwellings planned in development areas | **5.17 million** |
| Planned dwellings not yet materialised | **3.49 million (67.5%)** |
| Median municipality's pending share | **72.1%** |
| Planned capacity relative to existing housing stock | **33.4%** |
| Development land that has not started urbanisation | **48.8%** (area-weighted) |
| Municipalities where more than 80% of planned dwellings are pending | **35.7%** |

The 5.17 million planned dwellings sit in 256,606 hectares of development land. If every pending dwelling were built, the housing stock of these 431 municipalities would grow by about a third. Two-thirds of the pipeline has not been materialised.

This is not a rural artefact. Madrid alone has 158,113 pending dwellings; Murcia 111,116; Toledo 88,698. Toledo's plan envisages more than twice the city's existing stock.

### External check

MIVAU publishes its own national aggregate for the same source. Across **5,900 reporting municipalities** it counts **9.60 million planned dwellings and 7.09 million pending**, a pending share of **73.9%**, with **55.9%** of development land not started.

The 431 municipalities analysed here account for **53.8% of that national planned capacity** and 49.2% of the pending stock. So this is not a niche sample, and it is not a different universe: the national pipeline is, if anything, slightly *more* unbuilt than the urban one. The 5.17 million figure is a subset of the 9.60 million, not a competing estimate.

## What the rent data say

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

### 3. The panel does not rescue the hypothesis

I also estimated whether population growth passes through into rents more strongly where land is restricted, with municipality fixed effects and either year or province-year fixed effects. The interaction is never positive and significant:

- Non-urbanizable share × population growth: **−0.17** with province-year FE (p = 0.004).
- Planned capacity × population growth: **−0.10** with year FE (p = 0.003), but **−0.03** (p = 0.24) once province-year shocks are absorbed.
- Pending share × population growth: indistinguishable from zero.

A negative interaction is consistent with supply responding where capacity exists, but it is fragile to regional shocks. I do not claim it as a supply-elasticity estimate.

### 4. Demand growth does not close the gap

Fast-growing municipalities do plan more: the top tercile of population growth has a median of 375 planned dwellings per 1,000 existing, against 309 in declining municipalities. But the pending share barely moves: **71.3%** in fast-growing places versus **75.1%** in declining ones. The pipeline is not a rural curiosity that demand would clear.

## Interpretation

The Spanish planning system produces a lot of **paper housing**: land classified, sectors drawn, dwellings counted, and a large share of it never converted into buildings. The observable bottleneck in these data is not the headline stock of classified land. It is the step between permission and construction.

That reframes the policy question. If the debate is about how much land is classified as urbanizable, the data suggest the debate is aimed at the wrong margin. The margin that shows up is execution: land assembly, infrastructure, financing, the sequencing of plan approval, and the incentives of landowners to build rather than hold. The data cannot tell us which of these dominates. They can tell us that the classification share is not a good proxy for the constraint.

It also explains why the naive cross-section is so misleading. Land classification is not assigned to municipalities; it is chosen by them, in response to demand, geography and politics. A municipality that expects to grow classifies land. A municipality that is rural, protected or shrinking does not. Regressing rents on that choice without a source of exogenous variation mostly recovers the urban–rural gradient.

## What this does not prove

- **No causal effect of land classification on rents.** The design is cross-sectional and the treatment is endogenous. The null is not evidence that classification does not matter; it is evidence that this design cannot detect it.
- **No corruption claim.** Nothing here measures corruption, influence or wrongdoing. The gap between planned and built housing is consistent with many explanations, including the 2008 crash, slow infrastructure, financing constraints and rational landowners.
- **The pending variable is a stock, not a delay.** `munnvivpnd` counts dwellings planned in development areas that have not been materialised at the date of the SIU image. It does not say when they were planned, or whether they were ever expected to be built soon.
- **The SIU is a snapshot.** Land classification is measured around 2020–2025, while rents run to 2024. Any panel design using this measure is compromised by the fact that the "treatment" is observed after part of the outcome.
- **The sample is urban.** 431 municipalities, not all 8,000. They are the INE urban-indicator municipalities, and they hold 15.5 million dwellings.
- **Rent is not affordability.** I do not observe municipal household income, so I cannot compute rent-to-income. The outcome is rent per square metre.

## Reproduce

```bash
python -m pip install -r requirements.txt
python src/run_all.py
python -m pytest tests -q
```

`run_all.py` downloads the raw files into `data/raw/` (about 50 MB, cached), builds the panel, estimates the models, writes `outputs/results.json`, and redraws the figures. The pipeline works offline after the first run.

## Files

```
src/config.py          paths, indicators, province codes
src/download_data.py   downloads + sha256 manifest
src/build_panel.py     parses INE, maps codes, builds panel and cross-section
src/analysis.py        descriptives, regressions, results.json
src/figures.py         six figures
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

---

## Resumen en español

El sistema urbanístico español permite a los municipios decidir qué suelo se puede construir. La crítica habitual es que esa discrecionalidad restringe la oferta y encarece el alquiler. Con datos oficiales del SIU (5.898 municipios) y del INE (434 municipios urbanos, 2010–2025), el proyecto comprueba que **esa relación no aparece** una vez se compara dentro de la provincia y se controla el grado de urbanización. La correlación bruta va en sentido contrario porque el porcentaje de suelo no urbanizable es, sobre todo, una medida de ruralidad.

Lo que sí aparece es un problema distinto y más concreto: **5,17 millones de viviendas están planificadas en áreas de desarrollo y 3,49 millones (67,5%) no se han materializado**. El 48,8% del suelo de desarrollo ni siquiera ha iniciado la urbanización. En los municipios que más crecen, el 71,3% de la vivienda planificada sigue pendiente, frente al 75,1% en los que decrecen. El cuello de botella observable no es la cantidad de suelo clasificado, sino el paso entre el permiso y la construcción.

El proyecto no afirma causalidad, no mide corrupción y no dice que la clasificación del suelo sea irrelevante. Dice que un corte transversal municipal no permite identificarlo, y que el debate público está mirando el margen equivocado.
