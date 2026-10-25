# DATA.md — sources, semantics and merge

The Spanish core (§1–§5) documents five official public sources; four are used in
the model (IPVA is cached but unused). The comparative chapter (§6) adds four more.
All are free and downloaded by `src/download_data.py`; sha256 hashes are in
`data/raw/manifest.json`.

---

## 1. MIVAU — Sistema de Información Urbana (SIU)

**URL (alphanumeric workbook):**
`https://cdn.mivau.gob.es/portal-web-mivau/urbanismo-suelo/Datos%20alfanumericos%20SIU%20-%20Excel%20-%2020260619.zip`

**Publisher:** Ministerio de Vivienda y Agenda Urbana.
**Format:** ZIP with ~40 `.xlsx`, national / CCAA / province / municipality sheets.
**Used files:** `clases_suelo_mun.xlsx`, `areas_desarrollo_mun.xlsx`, `plan_mun.xlsx`.
**Metadata files (read, not parsed):** `Metadadatos clases de suelo.xlsx`,
`Metadatos areas desarrollo.xlsx`.

### `clases_suelo_mun.xlsx` — 5,898 municipalities

One row per municipality. Key: `ProvINE` (4-digit province+municipality code;
zero-padded to 5 digits to match INE).

| Column | Metadata definition | Unit |
|---|---|---|
| `ProvINE` | INE municipality code | 4-digit code |
| `DenoMun` | Municipality name | text |
| `Planeamiento` | Planning instrument and year | text |
| `MunTotSue` | Total municipal area, sum of all land classes | **km²** (verified against known municipal areas) |
| `MunPrSuCon` | Consolidated urban land | % of municipal area |
| `MunPrADes` | Development areas (*áreas de suelo de desarrollo*) | % of municipal area |
| `MunPrSuNoC` | Non-consolidated urban land | % |
| `MunPrSuzDe` | Delimited/sectorised urbanizable land | % |
| `MunPrSuzNd` | Undelimited/non-sectorised urbanizable land | % |
| `MunPrSnUzb` | Non-urbanizable land | % |
| `MunPrOtr` | General systems and other unassigned land | % |
| `Fuente` | Source of the data | text |
| `FechaAct` | SIU update date | date |

**Verified identities (asserted in `tests/test_pipeline.py`):**

```
MunPrSuCon + MunPrSuNoC + MunPrSuzDe + MunPrSuzNd + MunPrSnUzb + MunPrOtr = 100
MunPrADes = MunPrSuNoC + MunPrSuzDe
```

`MunPrADes` is therefore **not** an additional class. It is the union of the two
development classes, repeated as an aggregate. Including it in a sum double
counts. This is the single most important semantic trap in the SIU and the
reason the project never adds the seven `MunPr*` columns together.

### `areas_desarrollo_mun.xlsx` — 5,898 municipalities

| Column | Meaning | Unit |
|---|---|---|
| `munsupadgr` | Surface of development areas | m² |
| `munnumviv` | Dwellings planned in development areas | count |
| `munnvivpnd` | Dwellings planned but **not materialised** | count |
| `munpradsnu` | Share of development area not yet started (urbanisation) | % |
| `dens_viv` | Planned residential density | dwellings/ha |
| `fechaimafo` | Date of the aerial image used | year |

`munnvivpnd` is a **stock at the date of the image**, not a flow of delays. The
project says so in the README, because the difference matters: the variable
cannot distinguish "planned in 2006 and stalled" from "planned in 2024 and not
yet due".

### Coverage and exclusions

- 5,898 of ~8,131 Spanish municipalities have SIU land-class data.
- The missing ones are mostly very small municipalities without a general plan
  or without a reported SIU record. They are not missing at random with respect
  to size, so the SIU sample over-represents municipalities with planning.
- MIVAU's own national aggregate (`areas_desarrollo_nac.xlsx`,
  `clases_suelo_nac.xlsx`) reports 5,900 municipalities, **9,600,382 planned
  dwellings and 7,090,504 pending** (73.9%). This is used as an external check:
  the 431-municipality sample is 53.8% of the national planned stock. The 5.17
  million figure is a subset, not a competing national estimate.
- The matched analysis sample is limited to the 434 INE urban-indicator
  municipalities, of which 431 match the SIU.

---

## 2. INE — Indicadores Urbanos, table 69330

**URL:** `https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/69330.csv`
**Format:** semicolon-separated CSV, UTF-8 (not Latin-1 — see below).
**Coverage:** 434 municipalities, 2010–2025, 23 indicators.

**Critical parsing detail:** numbers use Spanish formatting (`1.234.567,8`).
Reading this file with default pandas parsing silently produces wrong values
(`1.234` becomes `1.234`). `parse_ine_number()` in `src/build_panel.py` strips
thousands separators and converts the decimal comma. This was caught early and
is asserted by the test suite (rents and prices must be positive and in a
plausible range).

**Encoding detail:** the file is UTF-8. Reading it as Latin-1 corrupts 118 of
the 434 municipality names. This was detected when name matching to the Padrón
failed for exactly those 118.

### Indicators used

| INE label | Variable | Unit |
|---|---|---|
| Alquiler anual medio por metro cuadrado | `rent_m2_year` | €/m²/year |
| Alquiler mensual medio | `rent_month` | €/month |
| Mediana del alquiler anual por metro cuadrado | `rent_median_m2_year` | €/m²/year |
| Precio medio por metro cuadrado de la vivienda | `price_m2` | €/m² |
| Número de viviendas convencionales según Catastro | `stock_catastro` | dwellings |
| Proporción de viviendas vacías | `vacancy_rate` | % |
| Número total de hogares | `households` | households |
| Tamaño medio de los hogares | `household_size` | persons |

Indicators not used (crime rates, census stock, flat/unifamiliar split) are
mapped out and recorded in `outputs/coverage.json` under
`ua_indicators_dropped`, so the omission is explicit rather than accidental.

**Missingness:** 2025 rents are empty (the year is not closed). 2024 has 408
non-missing rent values out of 434. The cross-section uses 2024.

**Housing-stock coverage changes in 2023.** `stock_catastro` is available for
about 119 municipalities in 2010–2022 and for about 399 in 2023–2025. The jump is
a coverage expansion, not a construction boom. The absorption ratio (METHOD §1b)
therefore uses the 2023–2025 window for the headline and 2021–2025 on the smaller
consistently-covered set as a robustness check. Comparing stock across the 2022/2023
boundary would mix a real change with a sample change.

---

## 3. INE — Padrón municipal, table 29005

**URL:** `https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/29005.csv`
**Coverage:** 8,138 municipalities, 1996–2025, by sex.
**Used for:** municipal population (denominator, demand control, population
growth 2015–2024).

The municipality field is a single string: `28079 Madrid`. The code is the first
five characters; the name starts at character 7.

---

## 4. INE — Índice de Precios de Vivienda en Alquiler (IPVA), table 59060

Downloaded and cached but **not used in the baseline**. It is an index for
municipalities above 10,000 inhabitants, with a different base and coverage from
the Urban Indicators rent level. Mixing a level and an index in the same
regression would be a specification error; it is reserved for a future
within-municipality rent-trend robustness check.

---

## 5. MIVAU — SERPAVI, 2011–2024

**URL:**
`https://cdn.mivau.gob.es/portal-web-mivau/vivienda/serpavi/2026-03_09_bd_SERPAVI_2011-2024%20-%20DEFINITIVO%20WEB_v2.xlsx`

**Publisher:** Ministerio de Vivienda y Agenda Urbana.
**Format:** one 71 MB workbook with six sheets: `Metadatos`, `CCAA`, `Provincias`,
`Municipios`, `Distritos`, `Secciones censales`. Only `Municipios` is parsed.
**Concept:** *Sistema Estatal de Índices de Alquiler de Vivienda*, an exploitation
of tax sources (*Modelo 100*) linked to cadastral data. It is **not** an INE
operation and is independent of table 69330.

### `Municipios` sheet — 8,099 municipality rows, 284 columns

One column block per year (2011–2024) and per concept. The 2024 block used here:

| Column | Meaning | Unit |
|---|---|---|
| `CUMUN` | INE municipality code (5 digits) | code |
| `BI_ALVHEPCO_TVC_24` | Dwellings behind the estimate (collective residential buildings) | count |
| `ALQM2_LV_M_VC_24` | **Median monthly rent per m²** | €/m²/month |
| `ALQM2_LV_25_VC_24` / `_75_` | P25 / P75 of the same distribution | €/m²/month |
| `ALQTBID12_M_VC_24` | Median monthly rent per dwelling | €/month |
| `SLVM2_M_VC_24` | Median surface of the dwellings in the estimate | m² |

**Coverage and comparability:**

- 8,099 municipality rows, of which 2,555 publish a 2024 rent. The rest are
  suppressed for tax secrecy or have no qualifying rental stock.
- All **431** municipalities in the analysis cross-section have a SERPAVI rent;
  **406** also have an INE rent in 2024.
- The two series correlate at **0.991** in levels (0.992 in logs). Annualised,
  the median SERPAVI/INE ratio is **0.959**; a median of monthly rents and a mean
  of annual rents are not the same statistic, so exact equality is not expected.
- **Navarra and the Basque Country are excluded** from the tax-source tables
  because their foral tax regimes do not report to the common source. No
  municipality from those communities is in the analysis sample, so this does
  not bias the merge — but it does limit the national frame.
- Blue cells in the published workbook are censored cells, not zeros. They are
  read as missing.

The project uses SERPAVI as an **independent outcome series** for the rent null
(README section 2b), not as a second national estimate to be pooled with INE.

---

## 6. Comparative chapter — OECD and Eurostat

These sources are not part of the Spanish municipal analysis. They answer a
different question ("is Spain unusual?") and are documented separately so the two
designs cannot be confused.

### 6.1. OECD Analytical House Prices

**URL (SDMX CSV):**
`https://sdmx.oecd.org/public/rest/data/OECD.ECO.MPD,DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES,1.0/.A..?startPeriod=1990&format=csvfile`

**Publisher:** OECD, `DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES`.
**File:** `data/raw/oecd_house_prices.csv` (937,392 bytes).
**Coverage:** annual, 1990–2025.

| Column | Meaning |
|---|---|
| `REF_AREA` | ISO3 country code, plus aggregates |
| `MEASURE` | `HPI_YDH` price-to-income, `HPI_RPI` price-to-rent, `RHP` real house prices |
| `TIME_PERIOD` | year |
| `OBS_VALUE` | index value |
| `UNIT_MEASURE` | `IX` (index) |
| `BASE_PER` | 2015 |
| `ADJUSTMENT` | `S` (seasonally adjusted source series, annual) |

**Critical semantic point:** all three measures are **indices with base 2015 =
100**, not levels. The chapter compares changes (2015→latest, 2000→latest) and
never compares price-to-income levels across countries. The OECD price-to-rent
index uses a national rent deflator, not the municipal market rent series used in
the Spanish core; the two are not combined.

**Aggregates are not countries.** `EA`, `EA17`, `EA19`, `EA20`, `EU27_2020` and
`OECD` appear in `REF_AREA` and must be dropped. Keeping them inflates the sample
to 43 and changes the ranks (see ANALYSIS_LOG Session 13, bug 1). After the drop:

- price-to-income: **40 countries**;
- price-to-rent: **42 countries**;
- real house prices: **47 countries**, of which **40** also have price-to-income.

The 2000 observation exists for only **25** of the 40 price-to-income countries;
15 post-2000 EU members have no 2000 value. The chapter reports n = 25 for that
comparison rather than pretending it is the same sample.

### 6.2. Eurostat building permits

**URL:**
`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_cobp_a?format=JSON&lang=EN&indic_bt=BPRM_DW&cpa2_1=CPA_F41001_X_410014&unit=THS`

**File:** `data/raw/eurostat_permits.json` (15,307 bytes).
**Concept:** building permits, number of dwellings, residential buildings excluding
residences for communities; thousands; unadjusted.
**Frequency:** annual.

Filters: `indic_bt=BPRM_DW` (dwellings in residential buildings),
`cpa2_1=CPA_F41001_X_410014` (residential buildings), `unit=THS` (thousands).

The file is Eurostat JSON-stat 2.0: a `dimension` block with category indices and
a flat `value` object. `eurostat_tidy()` in `src/comparative.py` decodes it by
dimension position; a plain `pd.read_json` would lose the labels.

**Geographies:** 42, including `EA19`, `EA20`, `EA21` and `EU27_2020`. The
analysis keeps only ISO2 codes in `ISO2_TO_ISO3` (which also handles `EL` for
Greece and `UK` for the United Kingdom).

**Trap — 2025 is preliminary.** Spain's 2025 value is exactly 200.0 thousand,
against 179.4 thousand in 2024. That is a flash round number, not a completed
year. `PERMITS_LAST_COMPLETE_YEAR = 2024`, and 2025 is excluded from every window.

### 6.3. Eurostat population

**URL:**
`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_pjan?format=JSON&lang=EN&sex=T&age=TOTAL&unit=NR`

**File:** `data/raw/eurostat_population.json` (53,912 bytes).
**Concept:** population on 1 January, total, persons.
**Coverage:** 59 geographies, including aggregates and `DE_TOT`.

Merged to permits on `geo` and `year`; a country-year is used only when both the
permit count and the population are observed:

```
permits_per_1000 = permits_ths * 1,000,000 / population
```

**Coverage rule.** A window mean requires at least **three annual observations**
with a matching population. This is not cosmetic:

- Bosnia (`BA`) has permits but no Eurostat population series → no per-capita
  value in either window.
- The United Kingdom (`UK`) permit series ends in 2019 → absent from 2021–2024.
- Kosovo (`XK`) population ends in 2022 → fails the 2021–2024 rule.

Result: **34 countries** in 2015–2019 and **33** in 2021–2024, not the 38 that the
raw geography list suggests. The denominators are stored in `results.json`.

### 6.4. Eurostat Urban Audit — city price-to-rent

**URL:**
`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/urb_clivcon?format=JSON&lang=EN&indic_ur=SA1053V&indic_ur=SA1049V&indic_ur=DE3017V`

**File:** `data/raw/eurostat_urban_audit.json` (294,675 bytes).

| Indicator | Meaning | Unit |
|---|---|---|
| `SA1053V` | Average price for buying an apartment | EUR/m² |
| `SA1049V` | Average rent for housing | EUR/m² (label says annual; reporting is not consistent) |
| `DE3017V` | Population living in private households | persons |

**City codes are at least six characters** (`ES001C`, `DE001C`). Two-letter codes
are country aggregates and are dropped. The raw extract has **255 city rows**;
after requiring a positive price and rent, **251** are comparable across **six
countries**, of which **87** are Spanish.

**Trap — the rent label says annual, but the values are not.** Eurostat labels
`SA1049V` "Average annual rent for housing per m²". That label is not reliable
across countries: Germany and Portugal report about 8.5 EUR/m², which can only be a
monthly rent; Spain reports 82.5, Finland 187.9, Croatia 129.0 and Lithuania 113.5,
which are annual. Treating the label as authoritative would divide German rents by
12 relative to Spanish rents and destroy the comparison.

The project therefore computes the country median raw rent and applies a
country-level rule:

- median **< 20 EUR/m²** → monthly, multiply by 12;
- otherwise → annual.

The country medians separate cleanly: Germany 8.50 and Portugal 8.46 on the
monthly side; Spain 82.53, Finland 187.91, Croatia 129.00 and Lithuania 113.46 on
the annual side. The threshold sits in an empty interval (8.5 to 41.4).

**Latvia is excluded.** Its four cities imply gross yields from 2.3% to 17.8%
under a single unit, so the series is internally inconsistent. The four rows stay
in `comparative_cities.csv` with `rent_unit = "inconsistent"` and
`comparable = False`, and are excluded from the country medians and figures.

**Mixed years.** Each city uses its latest available year. The comparable sample
spans 2022–2025; Spain's median year is 2023, Germany's 2022. A common year would
drop Spain or Germany. The year is stored per city, and each ratio uses price and
rent from the same city and year.

**Conceptual mismatch.** The price is for buying an apartment; the rent is an
average rent for housing, not the rent of the same apartment. The ratio is a gross
yield in years, not a rent-to-income affordability measure.

---

## 7. The municipal code crosswalk

This is where municipal projects usually break.

- The SIU uses a 4-digit `ProvINE`. Zero-pad to 5 → direct match to INE.
- The Padrón CSV carries the 5-digit code in the municipality string → trivial.
- **The Urban Indicators CSV carries names only, no codes.**

INE's Tempus JSON API does carry the code:

```
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/69330?nult=1&tip=AM
```

The lookup was built from that JSON and cached as
`data/raw/ua_municipality_codes.csv`.

**The hard part:** 87 of the 434 Urban Indicator municipalities use non-numeric
Tempus codes (`ES069C`, `ES503C1`, …). For these, the name had to be matched
against the Padrón.

The matching procedure:

1. Normalise names (strip accents, uppercase, strip punctuation).
2. Tokenise, drop articles (`LA`, `EL`, `LOS`, `LAS`), sort tokens. This makes
   `Palmas de Gran Canaria, Las` and `Las Palmas de Gran Canaria` collide.
3. Only accept a key if it is **unique** within the 2025 Padrón (8,026 unique
   keys out of 8,138 municipalities; 36 duplicated names are excluded).
4. Two municipalities still failed token matching and were mapped by hand:
   `Castelló de la Plana → 12040`, `Palma de Mallorca → 07040`.

The pipeline raises an error if any name remains unmapped, rather than silently
dropping it. Result: 434/434 mapped.

**Two UA municipalities have no SIU record:** Isla Cristina (21042) and Carmona
(41024). They remain in the panel (which does not need land data) and drop out
of the cross-section. Hence 431, not 434.

---

## 8. Licence and reproducibility

All eight sources are public statistical data published by MIVAU, INE, the OECD
and Eurostat. The pipeline caches everything under `data/raw/` and never
re-downloads unless `--force` is passed, so results are reproducible offline.
Hashing every file means a silent upstream revision is detectable.
