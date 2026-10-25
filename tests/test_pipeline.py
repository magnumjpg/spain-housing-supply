"""Invariants for the housing / land-classification pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SIU = RAW / "siu"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
TABLES = OUT / "tables"


def _require(path: Path) -> Path:
    """Skip cleanly when an optional raw or generated file is absent."""
    if not path.exists():
        pytest.skip(f"missing input: {path.relative_to(ROOT)}")
    return path


@pytest.fixture(scope="module")
def classes() -> pd.DataFrame:
    return pd.read_excel(_require(SIU / "clases_suelo_mun.xlsx"))


@pytest.fixture(scope="module")
def areas() -> pd.DataFrame:
    return pd.read_excel(_require(SIU / "areas_desarrollo_mun.xlsx"))


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_csv(_require(PROC / "panel.csv"), dtype={"code": str})


@pytest.fixture(scope="module")
def cross_section() -> pd.DataFrame:
    return pd.read_csv(
        _require(PROC / "cross_section.csv"), dtype={"code": str, "province_code": str}
    )


@pytest.fixture(scope="module")
def results() -> dict:
    return json.loads(_require(OUT / "results.json").read_text(encoding="utf-8"))


def test_land_shares_sum_to_100(classes: pd.DataFrame) -> None:
    base = [
        "MunPrSuCon", "MunPrSuNoC", "MunPrSuzDe", "MunPrSuzNd",
        "MunPrSnUzb", "MunPrOtr",
    ]
    total = classes[base].sum(axis=1)
    assert total.between(99.99, 100.01).all(), total.describe()


def test_development_area_is_the_union_of_two_categories(classes: pd.DataFrame) -> None:
    diff = classes["MunPrADes"] - (classes["MunPrSuNoC"] + classes["MunPrSuzDe"])
    assert diff.abs().max() < 0.01


def test_pending_never_exceeds_planned(areas: pd.DataFrame) -> None:
    d = areas.dropna(subset=["munnvivpnd", "munnumviv"])
    assert (d["munnvivpnd"] <= d["munnumviv"] + 1e-6).all()


def test_panel_has_unique_municipality_year(panel: pd.DataFrame) -> None:
    assert not panel.duplicated(["code", "year"]).any()


def test_rents_and_prices_are_positive(cross_section: pd.DataFrame) -> None:
    for col in ["rent_m2_year", "price_m2", "stock_catastro", "population"]:
        s = cross_section[col].dropna()
        assert (s > 0).all(), col


def test_cross_section_is_large_enough(cross_section: pd.DataFrame) -> None:
    assert len(cross_section) >= 400
    assert cross_section["rent_m2_year"].notna().sum() >= 350


def test_shares_are_bounded(cross_section: pd.DataFrame) -> None:
    for col in ["share_nonurbanizable", "share_development_areas", "pending_share", "unstarted_share"]:
        s = cross_section[col].dropna()
        assert s.between(0, 1).all(), col


def test_pipeline_aggregates_are_consistent(results: dict) -> None:
    p = results["pipeline"]
    assert p["pending_dwellings_total"] <= p["planned_dwellings_total"]
    assert 0 < p["aggregate_pending_share"] < 1
    assert abs(
        p["aggregate_pending_share"]
        - p["pending_dwellings_total"] / p["planned_dwellings_total"]
    ) < 1e-9


def test_sample_is_a_subset_of_the_national_aggregate(results: dict) -> None:
    p, v = results["pipeline"], results["validation"]
    assert p["planned_dwellings_total"] <= v["planned_dwellings"]
    assert p["pending_dwellings_total"] <= v["pending_dwellings"]
    assert 0 < v["sample_planned_share_of_national"] < 1
    assert 0 < v["pending_share"] < 1
    # The sample is a large minority of national capacity, not a rounding error.
    assert v["sample_planned_share_of_national"] > 0.4


def test_plan_vintage_is_documented(results: dict) -> None:
    v = results["plan_vintage"]
    assert v["n"] > 300
    # Newer plans must show a higher pending share; this is the counter-
    # explanation the README relies on, so it is tested rather than assumed.
    assert v["corr_plan_age_pending_share"] < 0
    for row in v["bins"]:
        assert 0 <= row["median_pending_share"] <= 1
        assert row["n"] > 0


def test_results_have_required_sections(results: dict) -> None:
    required = {
        "meta", "coverage", "descriptives", "pipeline", "validation", "terciles",
        "provinces", "regressions", "panel", "responsiveness", "plan_vintage",
        "robustness", "serpavi",
    }
    assert required.issubset(results.keys())


def test_serpavi_is_a_genuine_cross_source_check(results: dict) -> None:
    v = results["serpavi"]["validation"]
    assert v["n_matched_to_cross_section"] >= 400
    assert v["pearson_rent_level"] > 0.95
    # SERPAVI is monthly EUR/m2, INE is annual EUR/m2. Annualised, the two should
    # agree closely but not be identical: different mean/median and different source.
    assert 0.85 < v["median_annualised_ratio_to_ine"] < 1.15
    assert v["median_dwellings_behind_estimate"] > 0


def test_serpavi_reproduces_the_rent_null(results: dict) -> None:
    regs = {r["id"]: r for r in results["serpavi"]["regressions"]}
    for measure in ("pending_share", "unstarted_share", "share_nonurbanizable"):
        assert regs[f"serpavi_rent_urban_{measure}"]["coef_per_sd"] < 0
    assert regs["serpavi_rent_urban_pending_share"]["p"] < 0.10


def test_all_regressions_report_inference(results: dict) -> None:
    for r in results["regressions"] + results["robustness"] + results["serpavi"]["regressions"]:
        assert r["n"] > 0
        assert np.isfinite(r["coef_per_sd"])
        assert np.isfinite(r["se"]) and r["se"] > 0
        assert 0 <= r["p"] <= 1


def test_absorption_ratio_is_large_and_right_skewed(results: dict) -> None:
    a = results["pipeline"]["absorption"]["main"]
    pos = a["positive_flow_sample"]
    # The point of the metric is that the pipeline is decades, not years, of
    # recent construction. Fail loudly if coverage collapses or the ratio does.
    assert pos["n_municipalities"] > 300
    assert 20 < pos["aggregate_years"] < 100
    assert pos["median_years"] > 20
    assert 0 < pos["p25_years"] < pos["median_years"] < pos["p75_years"]
    assert pos["p90_years"] > pos["p75_years"]
    r = results["pipeline"]["absorption"]["robustness"]
    assert r["n_municipalities"] > 100
    assert r["aggregate_years"] > 20


def test_absorption_reports_both_samples_and_the_excluded_group(results: dict) -> None:
    a = results["pipeline"]["absorption"]["main"]
    assert a["headline_sample"] == "positive_flow_sample"
    pos = a["positive_flow_sample"]
    all_stock = a["all_stock_observed_sample"]

    # The conflation this test exists to prevent: 3.49 M is the matched sample,
    # 3.17 M is the positive-flow ratio sample, and 3.39 M is all-stock observed.
    assert pos["n_municipalities"] == 359
    assert all_stock["n_municipalities"] == 396
    assert pos["n_municipalities"] != all_stock["n_municipalities"]

    for sample in (pos, all_stock):
        for key in (
            "n_municipalities", "pending_dwellings", "annual_net_additions",
            "aggregate_years", "median_years", "p25_years", "p75_years",
            "p90_years", "share_above_20_years", "share_above_50_years",
        ):
            assert key in sample, key
        # Both aggregates must equal pending / additions to within 0.05 years.
        assert sample["aggregate_years"] == pytest.approx(
            sample["pending_dwellings"] / sample["annual_net_additions"], abs=0.05
        )

    assert pos["aggregate_years"] == pytest.approx(45.66, abs=0.05)
    assert all_stock["aggregate_years"] == pytest.approx(52.22, abs=0.05)
    assert all_stock["aggregate_years"] > pos["aggregate_years"]

    # Backwards-compatible aliases used by comparative.py and the README table.
    assert a["n_municipalities"] == pos["n_municipalities"]
    assert a["aggregate_years"] == pytest.approx(pos["aggregate_years"])

    excluded = a["excluded_by_positive_flow_filter"]
    assert excluded["n_municipalities"] == 37
    assert excluded["n_municipalities"] == (
        all_stock["n_municipalities"] - pos["n_municipalities"]
    )
    assert excluded["pending_dwellings"] == pytest.approx(
        all_stock["pending_dwellings"] - pos["pending_dwellings"], abs=1.0
    )
    assert excluded["pending_dwellings"] == pytest.approx(217_377, abs=1.0)
    assert excluded["n_shrinking"] == 24
    assert excluded["n_zero_pending"] == 12
    assert excluded["n_zero_change"] == 1
    assert excluded["n_missing_pending"] == 1

    # The old note called this an upper bound. It is not one, and the docs
    # repeat the note's logic, so guard the wording at the source.
    assert "upper bound" not in a["note"].lower()


def test_absorption_2021_2025_also_has_both_samples(results: dict) -> None:
    r = results["pipeline"]["absorption"]["robustness"]
    for key in ("positive_flow_sample", "all_stock_observed_sample",
                "excluded_by_positive_flow_filter"):
        assert key in r
    for sample in (r["positive_flow_sample"], r["all_stock_observed_sample"]):
        assert "n_municipalities" in sample
        assert "aggregate_years" in sample
        assert sample["aggregate_years"] == pytest.approx(
            sample["pending_dwellings"] / sample["annual_net_additions"], abs=0.05
        )
    assert r["positive_flow_sample"]["n_municipalities"] == 115
    assert r["all_stock_observed_sample"]["n_municipalities"] == 119


def test_price_regressions_report_their_own_n(results: dict) -> None:
    price = [r for r in results["regressions"] if r["id"].startswith("price_urban_")]
    assert len(price) == 5
    for r in price:
        assert 300 < r["n"] <= 431
    # The merged cross-section is 431, but no price regression uses all of it.
    assert any(r["n"] < 431 for r in price)


def test_cross_section_table_carries_n() -> None:
    path = TABLES / "cross_section.csv"
    if not path.exists():
        pytest.skip("missing generated table: outputs/tables/cross_section.csv")
    t = pd.read_csv(path)
    assert "n" in t.columns
    price = t[t["id"].str.startswith("price_urban_")]
    assert len(price) == 5
    assert price["n"].between(300, 431).all()
    assert (price["n"] < 431).any()


def test_readme_exists() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert len(readme) > 1500
    assert "What this does not prove" in readme
