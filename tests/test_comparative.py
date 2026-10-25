"""Invariants for the comparative chapter.

These tests read the generated tables, not the raw files, so they fail if a
source revision silently changes the comparison the README relies on.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TABLES = OUT / "tables"


def _require(path: Path) -> Path:
    """Skip cleanly when a generated comparative file is absent."""
    if not path.exists():
        pytest.skip(f"missing generated input: {path.relative_to(ROOT)}")
    return path


@pytest.fixture(scope="module")
def countries() -> pd.DataFrame:
    return pd.read_csv(_require(TABLES / "comparative_countries.csv"))


@pytest.fixture(scope="module")
def cities() -> pd.DataFrame:
    return pd.read_csv(_require(TABLES / "comparative_cities.csv"))


@pytest.fixture(scope="module")
def city_countries() -> pd.DataFrame:
    return pd.read_csv(_require(TABLES / "comparative_city_countries.csv"))


@pytest.fixture(scope="module")
def summary() -> pd.DataFrame:
    return pd.read_csv(_require(TABLES / "comparative_summary.csv"))


@pytest.fixture(scope="module")
def results() -> dict:
    return json.loads(_require(OUT / "results.json").read_text(encoding="utf-8"))


def test_oecd_aggregate_codes_are_not_countries(countries: pd.DataFrame) -> None:
    aggregates = {"EA", "EA17", "EA19", "EA20", "EU27_2020", "OECD"}
    assert not aggregates & set(countries["iso3"])


def test_price_to_income_sample_and_spain_rank(countries: pd.DataFrame) -> None:
    s = countries.set_index("iso3").loc["ESP"]
    assert abs(s["price_to_income_chg_2015_pct"] - 25.89) < 0.05
    assert int(s["price_to_income_rank_2015"]) == 7
    assert int(countries["price_to_income_chg_2015_pct"].notna().sum()) == 40
    # The benchmark is the median of 40 countries, not of 43 including aggregates.
    assert 8.0 < countries["price_to_income_chg_2015_pct"].median() < 10.5


def test_price_to_income_2000_sample_is_smaller(countries: pd.DataFrame) -> None:
    # Fifteen post-2000 EU members have no 2000 observation. This is a real
    # coverage limit, not a bug, and the README must cite 25 countries.
    assert int(countries["price_to_income_chg_2000_pct"].notna().sum()) == 25
    s = countries.set_index("iso3").loc["ESP"]
    assert abs(s["price_to_income_chg_2000_pct"] - 56.26) < 0.05
    assert int(s["price_to_income_rank_2000"]) == 5


def test_real_house_price_uses_the_price_to_income_universe(
    countries: pd.DataFrame, results: dict
) -> None:
    # RHP alone covers 47 countries (including partner economies). The rank is
    # deliberately computed inside the 40-country price-to-income sample.
    s = countries.set_index("iso3").loc["ESP"]
    assert results["comparative"]["country_layer"]["spain"]["real_house_price_n_2015"] == 40
    assert int(s["real_house_price_rank_2015"]) == 15
    assert abs(s["real_house_price_chg_2015_pct"] - 43.03) < 0.05


def test_spain_is_below_its_2007_peak_on_price_to_income(countries: pd.DataFrame) -> None:
    s = countries.set_index("iso3").loc["ESP"]
    assert int(s["price_to_income_peak_year"]) == 2007
    assert s["price_to_income_latest"] < s["price_to_income_peak"]
    assert -18.0 < s["price_to_income_latest_vs_peak_pct"] < -17.0
    # Price-to-rent is a different story: it is within 2% of its 2007 peak.
    assert int(s["price_to_rent_peak_year"]) == 2007
    assert -2.5 < s["price_to_rent_latest_vs_peak_pct"] < -1.0


def test_permits_exclude_2025_and_respect_the_three_year_rule(countries: pd.DataFrame) -> None:
    assert countries["permits_latest_year"].max() == 2024
    assert int(countries["permits_per_1000_2015_2019"].notna().sum()) == 34
    assert int(countries["permits_per_1000_2021_2024"].notna().sum()) == 33
    # Bosnia has permits but no Eurostat population; the UK ends in 2019.
    assert pd.isna(countries.set_index("iso3").loc["BIH", "permits_per_1000_2021_2024"])
    assert pd.isna(countries.set_index("iso3").loc["GBR", "permits_per_1000_2021_2024"])


def test_spain_permits_and_2006_peak(countries: pd.DataFrame) -> None:
    s = countries.set_index("iso3").loc["ESP"]
    assert abs(s["permits_per_1000_2015_2019"] - 1.40) < 0.01
    assert abs(s["permits_per_1000_2021_2024"] - 2.64) < 0.01
    assert int(s["permits_rank_2021_2024"]) == 28
    assert int(s["permits_peak_year"]) == 2006
    assert abs(s["permits_peak"] - 16.70) < 0.02


def test_country_measures_are_in_plausible_ranges(countries: pd.DataFrame) -> None:
    assert countries["price_to_income_latest"].dropna().between(40, 200).all()
    assert countries["permits_per_1000_2021_2024"].dropna().between(0, 30).all()


def test_city_coverage(cities: pd.DataFrame, city_countries: pd.DataFrame) -> None:
    assert len(cities) == 255
    comparable = cities[cities["comparable"]]
    assert len(comparable) == 251
    assert comparable["country"].nunique() == 6
    assert int((cities["country"] == "ES").sum()) == 87
    assert int((cities["country"] == "LV").sum()) == 4
    assert len(city_countries) == 6


def test_rent_unit_rule_is_country_level(cities: pd.DataFrame) -> None:
    assert (cities.groupby("country")["rent_unit"].nunique() == 1).all()
    expected = {
        "DE": "monthly", "PT": "monthly",
        "ES": "annual", "FI": "annual", "HR": "annual", "LT": "annual",
        "LV": "inconsistent",
    }
    assert cities.groupby("country")["rent_unit"].first().to_dict() == expected


def test_latvia_is_excluded_from_the_comparable_sample(cities: pd.DataFrame) -> None:
    lv = cities[cities["country"] == "LV"]
    assert (~lv["comparable"]).all()
    assert lv["rent_unit"].eq("inconsistent").all()
    # The exclusion must not leak into the country medians.
    assert "LV" not in set(
        pd.read_csv(TABLES / "comparative_city_countries.csv")["country"]
    )


def test_city_price_to_rent_ranges(cities: pd.DataFrame) -> None:
    comparable = cities[cities["comparable"]]
    assert comparable["price_to_rent"].notna().all()
    assert comparable["price_to_rent"].between(5, 60).all()
    spain = cities[cities["country"] == "ES"]
    assert abs(spain["price_to_rent"].median() - 16.56) < 0.02
    assert spain["price_to_rent"].between(10, 30).all()


def test_city_country_medians(city_countries: pd.DataFrame) -> None:
    medians = city_countries.set_index("country")["median_price_to_rent"]
    assert abs(medians["ES"] - 16.56) < 0.02
    assert abs(medians["DE"] - 29.48) < 0.02
    assert medians["FI"] < medians["ES"] < medians["DE"]


def test_city_years_are_mixed(cities: pd.DataFrame) -> None:
    # A single common year would drop either Spain (2023) or Germany (2022).
    years = set(cities[cities["comparable"]]["year"].unique())
    assert {2022, 2023, 2024, 2025} <= years


def test_greater_city_units_are_flagged(cities: pd.DataFrame) -> None:
    # The mix is documented, so it has to be recoverable from the table.
    comparable = cities[cities["comparable"]]
    assert comparable["greater_city"].sum() == 44
    assert comparable[comparable["country"] == "ES"]["greater_city"].sum() == 25
    assert comparable[comparable["country"] == "PT"]["greater_city"].all()


def test_municipal_only_sensitivity(results: dict) -> None:
    # Dropping greater-city aggregates removes every Portuguese city, so this is
    # a five-country check, not a better estimate of the same thing.
    sens = results["comparative"]["city_layer"]["municipal_only_sensitivity"]
    assert sens["n_cities"] == 207
    assert sens["n_countries"] == 5
    assert sens["rank_direction"] == "1 = highest"
    assert sens["spain_rank"] == 3
    by_country = {r["country"]: r["price_to_rent"] for r in sens["country_medians"]}
    assert "PT" not in by_country
    assert abs(by_country["ES"] - 16.06) < 0.02
    assert by_country["DE"] > by_country["HR"] > by_country["ES"] > by_country["LT"] > by_country["FI"]


def test_summary_has_one_row_per_headline_metric(summary: pd.DataFrame) -> None:
    assert list(summary["key"]) == [
        "price_to_income_2015",
        "price_to_income_2000",
        "price_to_rent_2015",
        "real_house_price_2015",
        "permits_2015_2019",
        "permits_2021_2024",
        "city_price_to_rent",
        "pipeline_years",
        "pipeline_dwellings",
    ]
    for _, row in summary.iterrows():
        if pd.notna(row["spain_rank"]):
            assert 1 <= int(row["spain_rank"]) <= int(row["rank_n"])
            assert row["rank_direction"] == "1 = highest"
    # The city row is ranked among six country medians, not 87 Spanish cities.
    city = summary.set_index("key").loc["city_price_to_rent"]
    assert int(city["rank_n"]) == 6
    assert int(city["n"]) == 87


def test_summary_bridges_to_the_spanish_pipeline(
    summary: pd.DataFrame, results: dict
) -> None:
    rows = summary.set_index("key")
    absorption = results["pipeline"]["absorption"]["main"]
    assert abs(rows.loc["pipeline_years", "spain"] - absorption["aggregate_years"]) < 1e-9
    assert abs(
        rows.loc["pipeline_dwellings", "spain"]
        - results["pipeline"]["pending_dwellings_total"]
    ) < 1e-9
    assert rows.loc["pipeline_years", "n"] == absorption["n_municipalities"]


def test_results_comparative_schema(results: dict) -> None:
    comparative = results["comparative"]
    assert comparative["meta"]["role"].startswith("Comparative chapter")
    assert comparative["country_layer"]["price_measures"]["n_countries_price_to_income"] == 40
    assert comparative["country_layer"]["permits"]["n_countries_2021_2024"] == 33
    assert comparative["city_layer"]["n_city_codes_raw"] == 843
    assert comparative["city_layer"]["n_cities_with_matched_price_and_rent"] == 255
    assert comparative["city_layer"]["n_cities_comparable"] == 251
    assert comparative["city_layer"]["n_countries_comparable"] == 6
    assert comparative["city_layer"]["excluded_cities"] == 4
    assert len(comparative["synthesis"]) == 9
    assert comparative["country_layer"]["spain"]["price_to_income_chg_2015_pct"] > 0


def test_endpoint_sensitivity_is_reported(results: dict) -> None:
    # Most series end in 2025, but not all; the benchmark must not depend on it.
    sens = results["comparative"]["country_layer"]["price_measures"]["endpoint_sensitivity"]
    pi = sens["price_to_income"]
    assert pi["full_endpoint"] == 2025
    assert pi["n_all_endpoints"] == 40
    assert pi["n_at_full_endpoint"] == 36
    assert abs(pi["median_pct_all_endpoints"] - 9.28) < 0.05
    assert abs(pi["median_pct_at_full_endpoint"] - 10.62) < 0.05
    assert pi["endpoint_counts"]["2025"] == 36


def test_comparative_json_has_no_nan(results: dict) -> None:
    def walk(node) -> None:
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, float):
            assert not math.isnan(node) and not math.isinf(node)

    walk(results["comparative"])
