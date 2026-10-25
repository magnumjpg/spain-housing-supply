"""Multi-country comparison inside the housing project.

Two layers, both descriptive:

1. Country layer
   - OECD Analytical House Prices: price-to-income, price-to-rent and real
     house-price indices, 1990-2025. These are *indices* (2015 = 100), so the
     project compares changes, never levels.
   - Eurostat building permits for residential buildings, per 1,000
     inhabitants, 2005-2024. Permits are a flow, not completions.

2. City layer
   - Eurostat Urban Audit: price per m2, rent per m2 and population for the
     latest year in which both a price and a rent are observed.
   - The rent series is not unit-consistent across countries. The rule and the
     exception are documented in `harmonise_city_rents` and in DATA.md.

The comparison dimensions the Spanish pipeline. It does not identify a causal
effect of regulation on prices, and the code makes no such claim.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    CITY_COUNTRY_EXCLUDE,
    CITY_RENT_MONTHLY_THRESHOLD,
    COUNTRY_NAMES,
    ISO2_TO_ISO3,
    OECD_AGGREGATES,
    OUT,
    RAW,
    TABLES,
)

PERMITS_LAST_COMPLETE_YEAR = 2024
PERMITS_WINDOWS = {"2015_2019": (2015, 2019), "2021_2024": (2021, 2024)}
MEASURES = {
    "price_to_income": "HPI_YDH",
    "price_to_rent": "HPI_RPI",
    "real_house_price": "RHP",
}
CITY_INDICATORS = {
    "SA1053V": "price_m2",
    "SA1049V": "rent_m2_raw",
    "DE3017V": "population",
}


def jsonable(obj):
    """Convert numpy / pandas scalars so json.dumps never chokes."""
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj


def eurostat_tidy(path: Path) -> pd.DataFrame:
    """Decode a Eurostat JSON-stat file into a long table.

    The `value` keys are flat indices over the dimensions in the order they
    appear in `dimension`. With API-filtered files the dimension sizes are the
    filtered sizes, so the same decoder works on both full and filtered data.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    dims = list(payload["dimension"].keys())
    sizes = [len(payload["dimension"][d]["category"]["index"]) for d in dims]

    rows = []
    for key, value in payload["value"].items():
        index = int(key)
        coords = []
        for size in reversed(sizes):
            coords.append(index % size)
            index //= size
        rows.append(list(reversed(coords)) + [value])

    df = pd.DataFrame(rows, columns=dims + ["value"])
    for dim in dims:
        category = payload["dimension"][dim]["category"]
        inverse = {pos: code for code, pos in category["index"].items()}
        labels = category.get("label", {})
        df[dim] = df[dim].map(inverse)
        df[f"{dim}_label"] = df[dim].map(labels)
    return df


def oecd_panel(path: Path) -> pd.DataFrame:
    """Annual OECD house-price measures, excluding aggregates."""
    df = pd.read_csv(path, dtype={"TIME_PERIOD": str}, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    df = df[df["FREQ"] == "A"].copy()
    df["year"] = pd.to_numeric(df["TIME_PERIOD"].str[:4], errors="coerce")
    df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    df = df[df["year"].notna() & ~df["REF_AREA"].isin(OECD_AGGREGATES)]
    return df


def _measure_table(df: pd.DataFrame, measure: str, prefix: str) -> pd.DataFrame:
    """Latest value, 2015 and 2000 levels, and changes for one OECD measure."""
    s = df[df["MEASURE"] == measure]
    piv = s.pivot_table(index="REF_AREA", columns="year", values="OBS_VALUE", aggfunc="first")
    latest_year = piv.apply(lambda row: row.last_valid_index(), axis=1)

    out = pd.DataFrame(index=piv.index)
    out[f"{prefix}_latest_year"] = latest_year
    out[f"{prefix}_latest"] = [
        piv.loc[code, latest_year[code]] if pd.notna(latest_year[code]) else np.nan
        for code in piv.index
    ]
    for year in (2000, 2015):
        out[f"{prefix}_{year}"] = piv[year] if year in piv.columns else np.nan
    out[f"{prefix}_chg_2015_pct"] = (out[f"{prefix}_latest"] / out[f"{prefix}_2015"] - 1) * 100
    out[f"{prefix}_chg_2000_pct"] = (out[f"{prefix}_latest"] / out[f"{prefix}_2000"] - 1) * 100

    # Own-history peak. This is what keeps the cross-country comparison honest:
    # a ratio can be above the OECD median and still below its own 2007 peak.
    peak_year = piv.apply(
        lambda row: row.idxmax() if row.notna().any() else np.nan, axis=1
    )
    out[f"{prefix}_peak_year"] = peak_year
    out[f"{prefix}_peak"] = [
        piv.loc[code, peak_year[code]] if pd.notna(peak_year[code]) else np.nan
        for code in piv.index
    ]
    out[f"{prefix}_latest_vs_peak_pct"] = (out[f"{prefix}_latest"] / out[f"{prefix}_peak"] - 1) * 100
    return out


def permits_panel(permits: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    """Country-year permits per 1,000 inhabitants, complete years only.

    The 2025 values are excluded because they are preliminary (Spain's 2025
    value is exactly 200.0 thousand, a flash round number, against 179.4
    thousand in 2024). A country-year is kept only when both the permit count
    and the population are observed.
    """
    p = permits.copy()
    p["year"] = pd.to_numeric(p["time"], errors="coerce")
    p["permits_ths"] = pd.to_numeric(p["value"], errors="coerce")
    p = p[p["year"] <= PERMITS_LAST_COMPLETE_YEAR]
    p = p[p["geo"].isin(ISO2_TO_ISO3)]

    pop = population.copy()
    pop["year"] = pd.to_numeric(pop["time"], errors="coerce")
    pop["population"] = pd.to_numeric(pop["value"], errors="coerce")
    pop = pop.groupby(["geo", "year"], as_index=False)["population"].sum()
    p = p.merge(pop, on=["geo", "year"], how="left")
    p["permits_per_1000"] = p["permits_ths"] * 1e6 / p["population"]
    p["iso3"] = p["geo"].map(ISO2_TO_ISO3)
    return p


def country_table(oecd: pd.DataFrame, permits: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    """One row per country: OECD price measures + Eurostat permits per 1,000."""
    frames = [_measure_table(oecd, code, name) for name, code in MEASURES.items()]
    out = pd.concat(frames, axis=1)

    p = permits_panel(permits, population)

    permit_rows = []
    for iso2, group in p.groupby("geo"):
        row = {"iso2": iso2, "iso3": ISO2_TO_ISO3[iso2]}
        for label, (start, end) in PERMITS_WINDOWS.items():
            values = group[group["year"].between(start, end)]["permits_per_1000"].dropna()
            # Require at least three annual observations so a single flash
            # year cannot define a window.
            row[f"permits_per_1000_{label}"] = values.mean() if len(values) >= 3 else np.nan
        values = group.dropna(subset=["permits_per_1000"])
        if len(values):
            row["permits_peak"] = values["permits_per_1000"].max()
            row["permits_peak_year"] = int(values.loc[values["permits_per_1000"].idxmax(), "year"])
            row["permits_latest_year"] = int(values["year"].max())
            row["permits_latest"] = float(values.loc[values["year"].idxmax(), "permits_per_1000"])
        permit_rows.append(row)
    permit_table = pd.DataFrame(permit_rows).set_index("iso3")

    out = out.join(permit_table, how="outer")
    out.index.name = "iso3"
    out = out.reset_index()
    out["iso2"] = out["iso3"].map({v: k for k, v in ISO2_TO_ISO3.items()})
    out["country"] = out["iso3"].map(COUNTRY_NAMES).fillna(out["iso3"])

    # Ranks are computed inside the sample each metric is actually compared on.
    # The real house-price comparison is restricted to countries that also have
    # a price-to-income series, so all price rows share one country universe
    # instead of mixing OECD members with partner economies.
    ydh_sample = out["price_to_income_chg_2015_pct"].notna()
    real_sample = ydh_sample & out["real_house_price_chg_2015_pct"].notna()
    rank_specs = [
        ("price_to_income_chg_2015_pct", "price_to_income_rank_2015", ydh_sample),
        ("price_to_income_chg_2000_pct", "price_to_income_rank_2000",
         out["price_to_income_chg_2000_pct"].notna()),
        ("price_to_rent_chg_2015_pct", "price_to_rent_rank_2015",
         out["price_to_rent_chg_2015_pct"].notna()),
        ("real_house_price_chg_2015_pct", "real_house_price_rank_2015", real_sample),
        ("permits_per_1000_2021_2024", "permits_rank_2021_2024",
         out["permits_per_1000_2021_2024"].notna()),
        ("permits_per_1000_2015_2019", "permits_rank_2015_2019",
         out["permits_per_1000_2015_2019"].notna()),
    ]
    for column, rank_column, sample in rank_specs:
        out[rank_column] = np.nan
        out.loc[sample, rank_column] = out.loc[sample, column].rank(
            ascending=False, method="min"
        )

    columns = [
        "iso3", "iso2", "country",
        "price_to_income_latest_year", "price_to_income_latest",
        "price_to_income_2015", "price_to_income_2000",
        "price_to_income_chg_2015_pct", "price_to_income_chg_2000_pct",
        "price_to_income_rank_2015", "price_to_income_rank_2000",
        "price_to_income_peak", "price_to_income_peak_year",
        "price_to_income_latest_vs_peak_pct",
        "price_to_rent_latest_year", "price_to_rent_latest",
        "price_to_rent_2015", "price_to_rent_chg_2015_pct",
        "price_to_rent_rank_2015",
        "price_to_rent_peak", "price_to_rent_peak_year",
        "price_to_rent_latest_vs_peak_pct",
        "real_house_price_latest_year", "real_house_price_latest",
        "real_house_price_2015", "real_house_price_chg_2015_pct",
        "real_house_price_rank_2015",
        "real_house_price_peak", "real_house_price_peak_year",
        "real_house_price_latest_vs_peak_pct",
        "permits_per_1000_2015_2019", "permits_per_1000_2021_2024",
        "permits_latest", "permits_latest_year",
        "permits_peak", "permits_peak_year",
        "permits_rank_2015_2019", "permits_rank_2021_2024",
    ]
    return out[columns].sort_values("iso3").reset_index(drop=True)


def harmonise_city_rents(cities: pd.DataFrame) -> pd.DataFrame:
    """Apply the documented rent-unit rule and flag the excluded country.

    The Eurostat label is "Average annual rent for housing per m2 - EUR", but
    the raw country medians split into two groups: ~8.5 EUR/m2 (monthly
    reporters, Germany and Portugal) and >=41 EUR/m2 (annual reporters). The
    threshold of 20 therefore separates the two groups with a wide margin.

    Latvia is different: its four city values imply gross yields from 2.3% to
    17.8% under any single unit, so the series is internally inconsistent. It
    is kept in the table with `comparable = False` and excluded from the
    cross-country medians and figures.
    """
    out = cities.copy()
    country_median = out.groupby("country")["rent_m2_raw"].median()
    unit = country_median.map(
        lambda value: "monthly" if value < CITY_RENT_MONTHLY_THRESHOLD else "annual"
    )
    out["rent_unit"] = out["country"].map(unit)
    out.loc[out["country"].isin(CITY_COUNTRY_EXCLUDE), "rent_unit"] = "inconsistent"
    out["rent_m2_annual"] = np.where(
        out["rent_unit"] == "monthly", out["rent_m2_raw"] * 12, out["rent_m2_raw"]
    )
    out["price_to_rent"] = out["price_m2"] / out["rent_m2_annual"]
    out["comparable"] = ~out["country"].isin(CITY_COUNTRY_EXCLUDE)
    out["country_name"] = out["country"].map(ISO2_TO_ISO3).map(COUNTRY_NAMES)
    out["greater_city"] = out["city_name"].str.contains("greater city", case=False, na=False)
    out["city_name_clean"] = (
        out["city_name"].str.replace(r"\s*\(greater city\)\s*$", "", regex=True)
    )
    return out


def city_table(urban_audit: pd.DataFrame) -> pd.DataFrame:
    """Latest city observation with both a sale price and a rent."""
    df = urban_audit[urban_audit["cities"].str.len() >= 6].copy()
    df["city_code"] = df["cities"]
    df["city_name"] = df["cities_label"].fillna(df["cities"])
    df["country"] = df["cities"].str[:2]
    df["year"] = pd.to_numeric(df["time"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["indic_ur"].isin(CITY_INDICATORS)].copy()
    df["variable"] = df["indic_ur"].map(CITY_INDICATORS)

    wide = df.pivot_table(
        index=["city_code", "city_name", "country", "year"],
        columns="variable",
        values="value",
        aggfunc="first",
    ).reset_index()
    wide = wide.dropna(subset=["price_m2", "rent_m2_raw"])
    latest = wide.sort_values("year").groupby("city_code").tail(1).copy()
    latest = harmonise_city_rents(latest)

    columns = [
        "city_code", "city_name", "city_name_clean", "greater_city", "country",
        "country_name", "year", "price_m2", "rent_m2_raw", "rent_unit",
        "rent_m2_annual", "price_to_rent", "population", "comparable",
    ]
    return latest[columns].sort_values(["country", "price_to_rent"]).reset_index(drop=True)


def city_country_table(cities: pd.DataFrame) -> pd.DataFrame:
    """Country medians for the comparable city sample."""
    comp = cities[cities["comparable"]].copy()
    rows = []
    for country, group in comp.groupby("country"):
        rows.append({
            "country": country,
            "country_name": group["country_name"].iloc[0],
            "n_cities": int(len(group)),
            "median_price_to_rent": float(group["price_to_rent"].median()),
            "p25_price_to_rent": float(group["price_to_rent"].quantile(0.25)),
            "p75_price_to_rent": float(group["price_to_rent"].quantile(0.75)),
            "first_year": int(group["year"].min()),
            "last_year": int(group["year"].max()),
        })
    out = pd.DataFrame(rows).sort_values("median_price_to_rent").reset_index(drop=True)
    return out


def summary_table(countries: pd.DataFrame, city_countries: pd.DataFrame) -> pd.DataFrame:
    """The chapter's headline table: Spain against a benchmark and a rank.

    Each metric is ranked inside the sample it is compared on. In particular,
    real house prices are compared only across countries that also have a
    price-to-income series, so the four price rows share one country universe.
    """
    spain = countries[countries["iso3"] == "ESP"].iloc[0]
    price_sample = countries["price_to_income_chg_2015_pct"].notna()

    specs = [
        {
            "key": "price_to_income_2015",
            "metric": "Price-to-income, change 2015 to latest",
            "column": "price_to_income_chg_2015_pct",
            "sample": price_sample,
            "benchmark": "OECD median",
            "unit": "%",
            "source": "OECD Analytical House Prices",
        },
        {
            "key": "price_to_income_2000",
            "metric": "Price-to-income, change 2000 to latest",
            "column": "price_to_income_chg_2000_pct",
            "sample": countries["price_to_income_chg_2000_pct"].notna(),
            "benchmark": "OECD median",
            "unit": "%",
            "source": "OECD Analytical House Prices",
        },
        {
            "key": "price_to_rent_2015",
            "metric": "Price-to-rent, change 2015 to latest",
            "column": "price_to_rent_chg_2015_pct",
            "sample": countries["price_to_rent_chg_2015_pct"].notna(),
            "benchmark": "OECD median",
            "unit": "%",
            "source": "OECD Analytical House Prices",
        },
        {
            "key": "real_house_price_2015",
            "metric": "Real house price, change 2015 to latest",
            "column": "real_house_price_chg_2015_pct",
            "sample": price_sample & countries["real_house_price_chg_2015_pct"].notna(),
            "benchmark": "OECD median (price-to-income sample)",
            "unit": "%",
            "source": "OECD Analytical House Prices",
        },
        {
            "key": "permits_2015_2019",
            "metric": "Building permits per 1,000 inhabitants, 2015-2019",
            "column": "permits_per_1000_2015_2019",
            "sample": countries["permits_per_1000_2015_2019"].notna(),
            "benchmark": "European median",
            "unit": "per 1,000",
            "source": "Eurostat sts_cobp_a + demo_pjan",
        },
        {
            "key": "permits_2021_2024",
            "metric": "Building permits per 1,000 inhabitants, 2021-2024",
            "column": "permits_per_1000_2021_2024",
            "sample": countries["permits_per_1000_2021_2024"].notna(),
            "benchmark": "European median",
            "unit": "per 1,000",
            "source": "Eurostat sts_cobp_a + demo_pjan",
        },
    ]

    # One rank convention everywhere: 1 = highest value of the metric. That
    # matters because the metrics point in different policy directions (more
    # permits is not "worse"), so the reader needs the direction stated, not
    # inferred from the rank.
    rows = []
    for spec in specs:
        values = countries.loc[spec["sample"], spec["column"]]
        rank = values.rank(ascending=False, method="min")
        rows.append({
            "key": spec["key"],
            "metric": spec["metric"],
            "spain": float(spain[spec["column"]]),
            "benchmark": spec["benchmark"],
            "benchmark_value": float(values.median()),
            "unit": spec["unit"],
            "spain_rank": int(rank.loc[spain.name]),
            "rank_direction": "1 = highest",
            "rank_n": int(len(values)),
            "n": int(len(values)),
            "source": spec["source"],
        })

    es_city = city_countries[city_countries["country"] == "ES"].iloc[0]
    # Spain is ranked among the six country medians, not among its 87 cities.
    city_rank = city_countries["median_price_to_rent"].rank(
        ascending=False, method="min"
    )
    rows.append({
        "key": "city_price_to_rent",
        "metric": "City price-to-rent, latest available (years of rent)",
        "spain": float(es_city["median_price_to_rent"]),
        "benchmark": "Median of 6 country medians",
        "benchmark_value": float(city_countries["median_price_to_rent"].median()),
        "unit": "years",
        "spain_rank": int(city_rank[city_countries["country"] == "ES"].iloc[0]),
        "rank_direction": "1 = highest",
        "rank_n": int(len(city_countries)),
        "n": int(es_city["n_cities"]),
        "source": "Eurostat Urban Audit urb_clivcon",
    })

    # The Spanish pipeline has no comparable cross-country measure. It is the
    # bridge back to the main project, not a benchmark.
    results_path = OUT / "results.json"
    if results_path.exists():
        results = json.loads(results_path.read_text(encoding="utf-8"))
        absorption = results.get("pipeline", {}).get("absorption", {}).get("main", {})
        pending = results.get("pipeline", {}).get("pending_dwellings_total")
        if absorption:
            rows.append({
                "key": "pipeline_years",
                "metric": "Pending pipeline, years of supply at 2023-2025 net additions",
                "spain": float(absorption["aggregate_years"]),
                "benchmark": "No comparable cross-country measure",
                "benchmark_value": np.nan,
                "unit": "years",
                "spain_rank": None,
                "rank_direction": None,
                "rank_n": None,
                "n": int(absorption["n_municipalities"]),
                "source": "SIU + INE, this project",
            })
        if pending:
            rows.append({
                "key": "pipeline_dwellings",
                "metric": "Pending dwellings in the matched urban sample",
                "spain": float(pending),
                "benchmark": "No comparable cross-country measure",
                "benchmark_value": np.nan,
                "unit": "dwellings",
                "spain_rank": None,
                "rank_direction": None,
                "rank_n": None,
                "n": int(results["pipeline"]["n_municipalities"]),
                "source": "SIU + INE, this project",
            })

    return pd.DataFrame(rows, columns=[
        "key", "metric", "spain", "benchmark", "benchmark_value", "unit",
        "spain_rank", "rank_direction", "rank_n", "n", "source",
    ])


def build() -> dict:
    oecd = oecd_panel(RAW / "oecd_house_prices.csv")
    permits = eurostat_tidy(RAW / "eurostat_permits.json")
    population = eurostat_tidy(RAW / "eurostat_population.json")
    urban_audit = eurostat_tidy(RAW / "eurostat_urban_audit.json")

    countries = country_table(oecd, permits, population)
    cities = city_table(urban_audit)
    city_countries = city_country_table(cities)
    summary = summary_table(countries, city_countries)

    countries.to_csv(TABLES / "comparative_countries.csv", index=False, encoding="utf-8")
    cities.to_csv(TABLES / "comparative_cities.csv", index=False, encoding="utf-8")
    city_countries.to_csv(TABLES / "comparative_city_countries.csv", index=False, encoding="utf-8")
    summary.to_csv(TABLES / "comparative_summary.csv", index=False, encoding="utf-8")

    spain = countries[countries["iso3"] == "ESP"].iloc[0]
    spain_cities = cities[cities["country"] == "ES"]
    comparable_cities = cities[cities["comparable"]]
    excluded_cities = cities[~cities["comparable"]]
    bench = summary.set_index("key")["benchmark_value"]

    comparative = {
        "meta": {
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "role": "Comparative chapter inside the Spanish land project; not a separate project.",
            "note": (
                "All comparisons are descriptive. Cross-country associations do not identify "
                "a causal effect of regulation on prices."
            ),
        },
        "country_layer": {
            "price_measures": {
                "source": "OECD Analytical House Prices (DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES)",
                "unit": "index, 2015 = 100",
                "warning": (
                    "HPI_YDH, HPI_RPI and RHP are indices, not levels. The project compares "
                    "changes; it does not compare price-to-income levels across countries."
                ),
                "years": [int(oecd["year"].min()), int(oecd["year"].max())],
                "n_countries_price_to_income": int(countries["price_to_income_chg_2015_pct"].notna().sum()),
                "n_countries_price_to_rent": int(countries["price_to_rent_chg_2015_pct"].notna().sum()),
                "n_countries_real_house_price": int(
                    (
                        countries["price_to_income_chg_2015_pct"].notna()
                        & countries["real_house_price_chg_2015_pct"].notna()
                    ).sum()
                ),
            },
            "permits": {
                "source": "Eurostat sts_cobp_a (BPRM_DW, CPA_F41001_X_410014, THS) and demo_pjan",
                "unit": "dwellings per 1,000 inhabitants",
                "windows": {k: list(v) for k, v in PERMITS_WINDOWS.items()},
                "last_complete_year": PERMITS_LAST_COMPLETE_YEAR,
                "excluded_year": 2025,
                "excluded_reason": "2025 is preliminary; Spain's 2025 value is exactly 200.0 thousand.",
                "coverage_rule": (
                    "A window mean requires at least three annual observations with a matching "
                    "population. Bosnia has no Eurostat population series; the UK permit series "
                    "ends in 2019; Kosovo has population only to 2022."
                ),
                "n_countries_2015_2019": int(countries["permits_per_1000_2015_2019"].notna().sum()),
                "n_countries_2021_2024": int(countries["permits_per_1000_2021_2024"].notna().sum()),
            },
            "spain": {
                "price_to_income_chg_2015_pct": float(spain["price_to_income_chg_2015_pct"]),
                "price_to_income_chg_2000_pct": float(spain["price_to_income_chg_2000_pct"]),
                "price_to_income_rank_2015": int(spain["price_to_income_rank_2015"]),
                "price_to_income_n_2015": int(countries["price_to_income_chg_2015_pct"].notna().sum()),
                "price_to_rent_chg_2015_pct": float(spain["price_to_rent_chg_2015_pct"]),
                "price_to_rent_rank_2015": int(spain["price_to_rent_rank_2015"]),
                "price_to_rent_n_2015": int(countries["price_to_rent_chg_2015_pct"].notna().sum()),
                "real_house_price_chg_2015_pct": float(spain["real_house_price_chg_2015_pct"]),
                "real_house_price_rank_2015": int(spain["real_house_price_rank_2015"]),
                "real_house_price_n_2015": int(
                    (
                        countries["price_to_income_chg_2015_pct"].notna()
                        & countries["real_house_price_chg_2015_pct"].notna()
                    ).sum()
                ),
                "permits_per_1000_2015_2019": float(spain["permits_per_1000_2015_2019"]),
                "permits_rank_2015_2019": int(spain["permits_rank_2015_2019"]),
                "permits_n_2015_2019": int(countries["permits_per_1000_2015_2019"].notna().sum()),
                "permits_per_1000_2021_2024": float(spain["permits_per_1000_2021_2024"]),
                "permits_rank_2021_2024": int(spain["permits_rank_2021_2024"]),
                "permits_n_2021_2024": int(countries["permits_per_1000_2021_2024"].notna().sum()),
                "permits_peak": float(spain["permits_peak"]),
                "permits_peak_year": int(spain["permits_peak_year"]),
            },
            "spain_history": {
                "note": (
                    "Own-history peak, not a cross-country benchmark. Indices are 2015 = 100; "
                    "a ratio can be above the OECD median and still below its own 2007 peak."
                ),
                "price_to_income_peak": float(spain["price_to_income_peak"]),
                "price_to_income_peak_year": int(spain["price_to_income_peak_year"]),
                "price_to_income_latest_vs_peak_pct": float(spain["price_to_income_latest_vs_peak_pct"]),
                "price_to_rent_peak": float(spain["price_to_rent_peak"]),
                "price_to_rent_peak_year": int(spain["price_to_rent_peak_year"]),
                "price_to_rent_latest_vs_peak_pct": float(spain["price_to_rent_latest_vs_peak_pct"]),
                "real_house_price_peak": float(spain["real_house_price_peak"]),
                "real_house_price_peak_year": int(spain["real_house_price_peak_year"]),
                "real_house_price_latest_vs_peak_pct": float(spain["real_house_price_latest_vs_peak_pct"]),
            },
            "medians": {
                "price_to_income_chg_2015_pct": float(bench["price_to_income_2015"]),
                "price_to_income_chg_2000_pct": float(bench["price_to_income_2000"]),
                "price_to_rent_chg_2015_pct": float(bench["price_to_rent_2015"]),
                "real_house_price_chg_2015_pct": float(bench["real_house_price_2015"]),
                "permits_per_1000_2015_2019": float(bench["permits_2015_2019"]),
                "permits_per_1000_2021_2024": float(bench["permits_2021_2024"]),
            },
        },
        "city_layer": {
            "source": "Eurostat Urban Audit urb_clivcon",
            "indicators": {
                "price_m2": "SA1053V (average price for buying an apartment, EUR per m2)",
                "rent_m2": "SA1049V (average rent for housing, EUR per m2)",
                "population": "DE3017V",
            },
            "unit_rule": (
                "Country median raw rent < 20 EUR/m2 is treated as monthly and multiplied by 12; "
                "otherwise the value is annual. The two groups separate at ~8.5 and >=41 EUR/m2."
            ),
            "excluded_countries": {
                "LV": (
                    "Four cities imply gross yields from 2.3% to 17.8% under a single unit; "
                    "the series is internally inconsistent, not merely mislabelled."
                )
            },
            "year_note": (
                "Latest available year per city. The comparison mixes 2022-2025 because a common "
                "year would drop either Spain or Germany."
            ),
            "n_cities_raw": int(len(cities)),
            "n_cities_comparable": int(len(comparable_cities)),
            "n_countries_comparable": int(comparable_cities["country"].nunique()),
            "excluded_cities": int(len(excluded_cities)),
            "spain": {
                "n_cities": int(len(spain_cities)),
                "median_price_to_rent": float(spain_cities["price_to_rent"].median()),
                "p25_price_to_rent": float(spain_cities["price_to_rent"].quantile(0.25)),
                "p75_price_to_rent": float(spain_cities["price_to_rent"].quantile(0.75)),
                "median_year": int(spain_cities["year"].median()),
            },
            "country_medians": city_countries.to_dict(orient="records"),
        },
        "synthesis": summary.to_dict(orient="records"),
    }

    results_path = OUT / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    results["comparative"] = comparative
    results_path.write_text(
        json.dumps(jsonable(results), indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return comparative


def main() -> None:
    comparative = build()
    country = comparative["country_layer"]
    city = comparative["city_layer"]
    spain = country["spain"]
    print(f"Countries with price-to-income: {country['price_measures']['n_countries_price_to_income']}")
    print(f"Countries with permits 2021-2024: {country['permits']['n_countries_2021_2024']}")
    print(f"Spain price-to-income 2015->latest: {spain['price_to_income_chg_2015_pct']:.1f}% "
          f"(rank {spain['price_to_income_rank_2015']} of {spain['price_to_income_n_2015']})")
    print(f"Spain price-to-rent 2015->latest: {spain['price_to_rent_chg_2015_pct']:.1f}% "
          f"(rank {spain['price_to_rent_rank_2015']} of {spain['price_to_rent_n_2015']})")
    print(f"Spain real house price 2015->latest: {spain['real_house_price_chg_2015_pct']:.1f}% "
          f"(rank {spain['real_house_price_rank_2015']} of {spain['real_house_price_n_2015']})")
    print(f"Spain permits per 1,000 2021-2024: {spain['permits_per_1000_2021_2024']:.2f} "
          f"(rank {spain['permits_rank_2021_2024']} of {spain['permits_n_2021_2024']})")
    print(f"Cities: {city['n_cities_comparable']} comparable across "
          f"{city['n_countries_comparable']} countries; Spain {city['spain']['n_cities']} "
          f"median price-to-rent {city['spain']['median_price_to_rent']:.1f} years")
    print(f"Comparative tables written to {TABLES}")


if __name__ == "__main__":
    main()
