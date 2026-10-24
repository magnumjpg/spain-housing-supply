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


@pytest.fixture(scope="module")
def classes() -> pd.DataFrame:
    return pd.read_excel(SIU / "clases_suelo_mun.xlsx")


@pytest.fixture(scope="module")
def areas() -> pd.DataFrame:
    return pd.read_excel(SIU / "areas_desarrollo_mun.xlsx")


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_csv(PROC / "panel.csv", dtype={"code": str})


@pytest.fixture(scope="module")
def cross_section() -> pd.DataFrame:
    return pd.read_csv(PROC / "cross_section.csv", dtype={"code": str, "province_code": str})


@pytest.fixture(scope="module")
def results() -> dict:
    return json.loads((OUT / "results.json").read_text(encoding="utf-8"))


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
        "robustness",
    }
    assert required.issubset(results.keys())


def test_all_regressions_report_inference(results: dict) -> None:
    for r in results["regressions"] + results["robustness"]:
        assert r["n"] > 0
        assert np.isfinite(r["coef_per_sd"])
        assert np.isfinite(r["se"]) and r["se"] > 0
        assert 0 <= r["p"] <= 1


def test_readme_exists() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert len(readme) > 1500
    assert "What this does not prove" in readme
