# DATA.md — sources, semantics and merge

Every number in the project comes from the five public sources below. All are
official, free, and downloaded by `src/download_data.py`; sha256 hashes are in
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

## 6. The municipal code crosswalk

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

## 7. Licence and reproducibility

All five sources are public statistical data published by MIVAU and INE. The
pipeline caches everything under `data/raw/` and never re-downloads unless
`--force` is passed, so results are reproducible offline. Hashing every file
means a silent upstream revision is detectable.
