"""Estimate the descriptive regressions and write outputs/results.json.

Design (see METHOD.md):
  1. Cross-section 2024: rents, prices and rent-to-price ratios against five
     land / pipeline measures, with province fixed effects.
  2. Panel 2013-2024: does population growth pass through into rents more
     strongly where legal capacity is low? Municipality FE + year FE, and
     municipality FE + province-year FE.
  3. Responsiveness: is planned capacity related to recent demand growth?
  4. Pipeline anatomy: the gap between planned and materialised dwellings.

Everything here is associational. The cross-section cannot identify a causal
effect of land classification on rents.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS

from config import COASTAL_PROVINCES, OUT, PROC, SIU, TABLES

def load_national() -> dict:
    """MIVAU's own national aggregate, used as an external check.

    The workbook has one data row per geography. Reading it avoids the circular
    validation of checking our sum against itself.
    """
    path = SIU / "areas_desarrollo_nac.xlsx"
    df = pd.read_excel(path, header=None)
    header = [str(x).strip() for x in df.iloc[0]]
    row = dict(zip(header, df.iloc[1]))
    mun_label = str(row["MunEstud"])
    n_mun = int(re.search(r"(\d+)", mun_label).group(1))

    classes = pd.read_excel(SIU / "clases_suelo_nac.xlsx", header=None)
    cheader = [str(x).strip() for x in classes.iloc[0]]
    crow = dict(zip(cheader, classes.iloc[1]))

    planned = float(row["Enumviv"])
    pending = float(row["Envivpnd"])
    return {
        "source": "SIU areas_desarrollo_nac.xlsx / clases_suelo_nac.xlsx",
        "municipalities_reported": n_mun,
        "municipalities_reporting_share": mun_label,
        "planned_dwellings": planned,
        "pending_dwellings": pending,
        "pending_share": pending / planned,
        "development_area_ha": float(row["EaDes"]) / 1e4,
        "unstarted_share": float(row["Epradsnu"]) / 100,
        "total_municipal_area_km2": float(crow["ETotSue"]),
        "share_development_areas": float(crow["EPrADes"]) / 100,
        "share_nonurbanizable": float(crow["EPrSnUzb"]) / 100,
    }


MEASURES = {
    "share_nonurbanizable": "Share of municipal land classified non-urbanizable",
    "share_development_areas": "Share of municipal land in development areas",
    "planned_per_1000_stock": "Planned dwellings per 1,000 existing dwellings",
    "pending_share": "Share of planned dwellings not materialised",
    "unstarted_share": "Share of development land not yet started",
}

BASIC = ["log_population", "log_stock", "population_growth_15_24"]
URBAN = BASIC + ["log_density", "share_urban_consolidated"]


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


def zscore(s: pd.Series) -> pd.Series:
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd and np.isfinite(sd) else s * np.nan


def absorption_ratio(panel: pd.DataFrame, cs: pd.DataFrame, y0: int, y1: int) -> tuple[dict, pd.DataFrame]:
    """Pending dwellings divided by recent net housing additions per year.

    This is a stock-over-flow ratio, not a forecast. The denominator is the
    change in the Catastro conventional-dwelling stock, which nets out
    demolitions; gross completions are higher, so the ratio is an upper bound
    on years of supply. It is computed only where the stock is observed in both
    years. The 2023-2025 window is used for the headline because Catastro
    coverage expands sharply in 2023; the 2021-2025 window is a robustness
    check on the smaller consistently-covered set.
    """
    st = panel.pivot_table(index="code", columns="year", values="stock_catastro", aggfunc="first")
    d = st[[y0, y1]].dropna()
    add = (d[y1] - d[y0]) / (y1 - y0)
    m = cs[["code", "municipality_name", "planned_dwellings", "pending_dwellings"]].merge(
        add.rename("add_per_year"), on="code"
    )
    m = m[(m["add_per_year"] > 0) & (m["pending_dwellings"] > 0)].copy()
    m["years_to_absorb"] = m["pending_dwellings"] / m["add_per_year"]
    summary = {
        "window": [int(y0), int(y1)],
        "n_municipalities": int(len(m)),
        "pending_dwellings": float(m["pending_dwellings"].sum()),
        "annual_net_additions": float(m["add_per_year"].sum()),
        "aggregate_years": float(m["pending_dwellings"].sum() / m["add_per_year"].sum()),
        "median_years": float(m["years_to_absorb"].median()),
        "p25_years": float(m["years_to_absorb"].quantile(0.25)),
        "p75_years": float(m["years_to_absorb"].quantile(0.75)),
        "p90_years": float(m["years_to_absorb"].quantile(0.90)),
        "share_above_20_years": float((m["years_to_absorb"] > 20).mean()),
        "share_above_50_years": float((m["years_to_absorb"] > 50).mean()),
        "note": (
            "Pending dwellings / net annual change in the Catastro conventional-dwelling "
            "stock. Net additions subtract demolitions, so this is an upper bound on "
            "years of supply at the recent construction rate. It is not a forecast: "
            "demand can grow, plans can be revised, and part of the pending stock may "
            "never be built."
        ),
    }
    table = m.sort_values("years_to_absorb", ascending=False).copy()
    return summary, table


def fit_cs(
    df: pd.DataFrame,
    outcome: str,
    measure: str,
    controls: list[str],
    label: str,
    controls_label: str | None = None,
) -> dict:
    cols = [outcome, measure] + controls + ["province_code"]
    d = df.dropna(subset=cols).copy()
    d["z"] = zscore(d[measure])
    formula = f"{outcome} ~ z + " + " + ".join(controls) + " + C(province_code)"
    m = smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["province_code"]})
    coef = float(m.params["z"])
    lo, hi = m.conf_int().loc["z"]
    sd = float(d[measure].std(ddof=0))
    is_share = bool(d[measure].dropna().between(0, 1.5).all())
    return {
        "id": label,
        "outcome": outcome,
        "measure": measure,
        "controls": controls_label or ("urban" if controls == URBAN else "basic"),
        "n": int(m.nobs),
        "coef_per_sd": coef,
        "se": float(m.bse["z"]),
        "p": float(m.pvalues["z"]),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "pct_effect_per_sd": float(100 * (np.exp(coef) - 1)),
        "coef_per_pp": float(coef / (sd * 100)) if is_share else None,
        "coef_per_unit": float(coef / sd),
        "measure_sd": sd,
        "measure_mean": float(d[measure].mean()),
        "r2": float(m.rsquared),
    }


def fit_panel(panel: pd.DataFrame, cs: pd.DataFrame, measure: str, fe: str) -> dict:
    z = cs.set_index("code")[measure]
    z = (z - z.mean()) / z.std(ddof=0)
    p = panel[["code", "year", "population", "rent_m2_year"]].copy()
    p["measure_z"] = p["code"].map(z)
    p["log_rent"] = np.log(p["rent_m2_year"].where(p["rent_m2_year"] > 0))
    p["log_pop"] = np.log(p["population"].where(p["population"] > 0))
    p = p.sort_values(["code", "year"])
    p["dlog_pop"] = p.groupby("code")["log_pop"].diff()
    p["interaction"] = p["measure_z"] * p["dlog_pop"]
    p["province_code"] = p["code"].str[:2]
    p["province_year"] = p["province_code"] + "_" + p["year"].astype(str)
    p = p.dropna(subset=["log_rent", "dlog_pop", "measure_z"])

    d = p.set_index(["code", "year"])
    X = sm.add_constant(d[["dlog_pop", "interaction"]])
    if fe == "province_year":
        m = PanelOLS(d["log_rent"], X, entity_effects=True, other_effects=d[["province_year"]], drop_absorbed=True)
        label = "municipality + province-year FE"
    else:
        m = PanelOLS(d["log_rent"], X, entity_effects=True, time_effects=True, drop_absorbed=True)
        label = "municipality + year FE"
    res = m.fit(cov_type="clustered", cluster_entity=True)
    return {
        "measure": measure,
        "fe": label,
        "n": int(res.nobs),
        "entities": int(d.index.get_level_values(0).nunique()),
        "coef_interaction": float(res.params["interaction"]),
        "se": float(res.std_errors["interaction"]),
        "p": float(res.pvalues["interaction"]),
        "ci_lo": float(res.conf_int().loc["interaction", "lower"]),
        "ci_hi": float(res.conf_int().loc["interaction", "upper"]),
        "coef_dlog_pop": float(res.params["dlog_pop"]),
        "p_dlog_pop": float(res.pvalues["dlog_pop"]),
    }


def main() -> dict:
    cs = pd.read_csv(PROC / "cross_section.csv", dtype={"code": str, "province_code": str})
    panel = pd.read_csv(PROC / "panel.csv", dtype={"code": str, "province_code": str})
    coverage = json.loads((OUT / "coverage.json").read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Descriptives
    # ------------------------------------------------------------------
    desc_vars = [
        "rent_m2_year", "rent_month", "price_m2", "rent_to_price",
        "rent_m2_serpavi", "serpavi_n", "serpavi_m2",
        "share_nonurbanizable", "share_development_areas",
        "planned_dwellings", "pending_dwellings", "pending_share",
        "delivery_rate", "unstarted_share", "planned_per_1000_stock",
        "pending_per_1000_stock", "population", "density_pop_km2",
        "population_growth_15_24", "plan_age",
    ]
    descriptives = {}
    for v in desc_vars:
        s = cs[v].dropna()
        descriptives[v] = {
            "n": int(s.size),
            "mean": float(s.mean()),
            "median": float(s.median()),
            "p25": float(s.quantile(0.25)),
            "p75": float(s.quantile(0.75)),
            "min": float(s.min()),
            "max": float(s.max()),
            "sd": float(s.std(ddof=0)),
        }

    # ------------------------------------------------------------------
    # Pipeline anatomy
    # ------------------------------------------------------------------
    planned = cs["planned_dwellings"].sum()
    pending = cs["pending_dwellings"].sum()
    stock = cs["stock_catastro"].sum()
    dev_area = cs["dev_area_m2"].sum()
    w_unstarted = (cs["dev_area_m2"] * cs["unstarted_share"]).sum() / dev_area

    national = load_national()
    national["sample_planned_share_of_national"] = planned / national["planned_dwellings"]
    national["sample_pending_share_of_national"] = pending / national["pending_dwellings"]
    national["note"] = (
        "MIVAU national aggregate, 5,900 reporting municipalities. Used to check "
        "that the 431-municipality sample is a large subset and not a different "
        "universe. The sample is not a random draw."
    )

    absorption_main, absorption_table = absorption_ratio(panel, cs, 2023, 2025)
    absorption_rob, _ = absorption_ratio(panel, cs, 2021, 2025)

    top_pending = (
        cs.nlargest(10, "pending_dwellings")[
            ["municipality_name", "province", "planned_dwellings", "pending_dwellings", "pending_share", "rent_m2_year"]
        ]
        .round({"pending_share": 4, "rent_m2_year": 1})
        .to_dict(orient="records")
    )

    # Terciles of population growth
    cs["growth_tercile"] = pd.qcut(cs["population_growth_15_24"], 3, labels=["low", "mid", "high"])
    terciles = (
        cs.groupby("growth_tercile", observed=True)
        .agg(
            n=("code", "size"),
            population_growth=("population_growth_15_24", "median"),
            planned_per_1000_stock=("planned_per_1000_stock", "median"),
            pending_share=("pending_share", "median"),
            unstarted_share=("unstarted_share", "median"),
            rent_m2_year=("rent_m2_year", "median"),
        )
        .reset_index()
    )
    terciles["growth_tercile"] = terciles["growth_tercile"].astype(str)
    terciles_out = terciles.round(4).to_dict(orient="records")

    # Province table
    prov = (
        cs.groupby(["province_code", "province"])
        .agg(
            n_municipalities=("code", "size"),
            planned_dwellings=("planned_dwellings", "sum"),
            pending_dwellings=("pending_dwellings", "sum"),
            stock=("stock_catastro", "sum"),
            median_pending_share=("pending_share", "median"),
        )
        .reset_index()
    )
    prov["aggregate_pending_share"] = prov["pending_dwellings"] / prov["planned_dwellings"]
    prov["planned_to_stock"] = prov["planned_dwellings"] / prov["stock"]
    prov = prov.sort_values("planned_dwellings", ascending=False)
    provinces_out = prov.round(4).to_dict(orient="records")

    # ------------------------------------------------------------------
    # Cross-section regressions
    # ------------------------------------------------------------------
    regressions = []
    for measure in MEASURES:
        regressions.append(fit_cs(cs, "log_rent", measure, URBAN, f"rent_urban_{measure}"))
    for measure in MEASURES:
        regressions.append(fit_cs(cs, "log_price", measure, URBAN, f"price_urban_{measure}"))
    for measure in MEASURES:
        regressions.append(fit_cs(cs, "log_rent_to_price", measure, URBAN, f"yield_urban_{measure}"))
    for measure in MEASURES:
        regressions.append(fit_cs(cs, "log_rent", measure, BASIC, f"rent_basic_{measure}"))

    # ------------------------------------------------------------------
    # Independent outcome source: SERPAVI (tax records, not INE)
    # ------------------------------------------------------------------
    sv = cs.dropna(subset=["rent_m2_serpavi", "rent_m2_year"]).copy()
    sv_ratio = (sv["rent_m2_serpavi"] * 12) / sv["rent_m2_year"]
    serpavi_validation = {
        "source": "MIVAU SERPAVI 2011-2024, Municipios sheet, 2024",
        "definition": "ALQM2_LV_M_VC_24: median monthly rent per m2 of collective residential buildings, Modelo 100 tax records",
        "n_matched_to_cross_section": int(len(sv)),
        "pearson_rent_level": float(sv["rent_m2_serpavi"].corr(sv["rent_m2_year"])),
        "pearson_log_rent": float(sv["log_rent_serpavi"].corr(sv["log_rent"])),
        "median_annualised_ratio_to_ine": float(sv_ratio.median()),
        "p10_annualised_ratio_to_ine": float(sv_ratio.quantile(0.10)),
        "p90_annualised_ratio_to_ine": float(sv_ratio.quantile(0.90)),
        "median_dwellings_behind_estimate": float(sv["serpavi_n"].median()),
        "share_municipalities_n_below_30": float((sv["serpavi_n"] < 30).mean()),
        "excluded_autonomous_communities": ["Navarra", "País Vasco"],
        "note": (
            "SERPAVI is built from tax declarations (Modelo 100) and is independent "
            "of INE table 69330. It excludes Navarra and the Basque Country because "
            "those foral regimes do not report to the common tax source. Agreement "
            "in levels does not make the two series the same measurement: SERPAVI "
            "is a median of monthly rent per m2, INE is a mean annual rent per m2."
        ),
    }
    serpavi_regressions = []
    for controls, tag in ((URBAN, "urban"), (BASIC, "basic")):
        for measure in MEASURES:
            serpavi_regressions.append(
                fit_cs(cs, "log_rent_serpavi", measure, controls, f"serpavi_rent_{tag}_{measure}")
            )

    # ------------------------------------------------------------------
    # Panel interactions
    # ------------------------------------------------------------------
    panel_out = []
    for measure in MEASURES:
        for fe in ("year", "province_year"):
            panel_out.append(fit_panel(panel, cs, measure, fe))

    # ------------------------------------------------------------------
    # Responsiveness: does planning follow demand?
    # ------------------------------------------------------------------
    responsiveness = []
    for outcome in ["planned_per_1000_stock", "pending_share", "unstarted_share"]:
        d = cs.dropna(subset=[outcome, "population_growth_15_24", "log_population", "province_code"]).copy()
        m = smf.ols(
            f"{outcome} ~ population_growth_15_24 + log_population + C(province_code)",
            data=d,
        ).fit(cov_type="cluster", cov_kwds={"groups": d["province_code"]})
        responsiveness.append({
            "outcome": outcome,
            "n": int(m.nobs),
            "coef_pop_growth": float(m.params["population_growth_15_24"]),
            "se": float(m.bse["population_growth_15_24"]),
            "p": float(m.pvalues["population_growth_15_24"]),
            "r2": float(m.rsquared),
        })

    # ------------------------------------------------------------------
    # Plan vintage: a competing explanation for the pending share
    # ------------------------------------------------------------------
    v = cs.dropna(subset=["plan_age", "pending_share"]).copy()
    v["age_bin"] = pd.cut(
        v["plan_age"], [-1, 5, 10, 15, 20, 30, 200],
        labels=["<=5", "6-10", "11-15", "16-20", "21-30", ">30"],
    )
    vintage_bins = (
        v.groupby("age_bin", observed=True)
        .agg(
            n=("code", "size"),
            median_plan_age=("plan_age", "median"),
            median_pending_share=("pending_share", "median"),
            median_unstarted_share=("unstarted_share", "median"),
            median_planned_per_1000_stock=("planned_per_1000_stock", "median"),
        )
        .reset_index()
    )
    vintage_bins["age_bin"] = vintage_bins["age_bin"].astype(str)
    plan_vintage = {
        "n": int(len(v)),
        "corr_plan_age_pending_share": float(v["plan_age"].corr(v["pending_share"])),
        "corr_plan_age_unstarted_share": float(v["plan_age"].corr(v["unstarted_share"])),
        "median_plan_age": float(v["plan_age"].median()),
        "bins": vintage_bins.round(4).to_dict(orient="records"),
        "note": (
            "Newer plans have a higher pending share. This is consistent with "
            "capacity that has not had time to be built, and is a direct reason "
            "not to read the pending stock as obstruction."
        ),
    }

    # ------------------------------------------------------------------
    # Robustness of the two headline measures
    # ------------------------------------------------------------------
    robustness = []
    variants = {
        "exclude_madrid_barcelona": ~cs["code"].isin(["28079", "08019"]),
        "exclude_coastal_provinces": ~cs["province_code"].isin(COASTAL_PROVINCES),
        "population_above_50k": cs["population"] > 50_000,
        "add_plan_age": pd.Series(True, index=cs.index),
    }
    for name, mask in variants.items():
        sub = cs[mask].copy()
        controls = URBAN + (["plan_age"] if name == "add_plan_age" else [])
        for measure in ["share_nonurbanizable", "planned_per_1000_stock", "pending_share", "unstarted_share"]:
            r = fit_cs(
                sub, "log_rent", measure, controls, f"robust_{name}_{measure}",
                controls_label="urban + plan_age" if name == "add_plan_age" else "urban",
            )
            r["robustness"] = name
            robustness.append(r)

    # ------------------------------------------------------------------
    # Raw correlations (to show the naive association)
    # ------------------------------------------------------------------
    correlations = {}
    for measure in MEASURES:
        d = cs[[measure, "rent_m2_year", "price_m2", "log_rent"]].dropna()
        correlations[measure] = {
            "n": int(len(d)),
            "pearson_rent_level": float(d[measure].corr(d["rent_m2_year"])),
            "pearson_log_rent": float(d[measure].corr(d["log_rent"])),
            "pearson_price": float(d[measure].corr(d["price_m2"])),
        }

    results = {
        "meta": {
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "cross_section_year": 2024,
            "panel_years": [int(panel["year"].min()), int(panel["year"].max())],
            "measures": MEASURES,
            "controls": {"basic": BASIC, "urban": URBAN},
            "note": "All regressions are associational. See LIMITATIONS.md.",
        },
        "coverage": coverage,
        "descriptives": descriptives,
        "pipeline": {
            "n_municipalities": int(len(cs)),
            "planned_dwellings_total": float(planned),
            "pending_dwellings_total": float(pending),
            "aggregate_pending_share": float(pending / planned),
            "median_pending_share": float(cs["pending_share"].median()),
            "planned_to_stock": float(planned / stock),
            "pending_to_stock": float(pending / stock),
            "stock_total": float(stock),
            "development_area_ha": float(dev_area / 1e4),
            "median_unstarted_share": float(cs["unstarted_share"].median()),
            "weighted_unstarted_share": float(w_unstarted),
            "share_municipalities_pending_above_80": float((cs["pending_share"] > 0.8).mean()),
            "absorption": {"main": absorption_main, "robustness": absorption_rob},
            "top_pending": top_pending,
        },
        "validation": national,
        "serpavi": {
            "validation": serpavi_validation,
            "regressions": serpavi_regressions,
        },
        "terciles": terciles_out,
        "provinces": provinces_out,
        "regressions": regressions,
        "panel": panel_out,
        "responsiveness": responsiveness,
        "plan_vintage": plan_vintage,
        "robustness": robustness,
        "correlations": correlations,
    }

    (OUT / "results.json").write_text(
        json.dumps(jsonable(results), indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    pd.DataFrame(regressions).to_csv(TABLES / "cross_section.csv", index=False)
    pd.DataFrame(serpavi_regressions).to_csv(TABLES / "serpavi_rent.csv", index=False)
    pd.DataFrame(panel_out).to_csv(TABLES / "panel.csv", index=False)
    pd.DataFrame(robustness).to_csv(TABLES / "robustness.csv", index=False)
    pd.DataFrame(descriptives).T.to_csv(TABLES / "descriptives.csv")
    prov.to_csv(TABLES / "provinces.csv", index=False)
    pd.DataFrame(terciles_out).to_csv(TABLES / "growth_terciles.csv", index=False)
    pd.DataFrame([national]).to_csv(TABLES / "national_validation.csv", index=False)
    vintage_bins.to_csv(TABLES / "plan_vintage.csv", index=False)
    absorption_table.to_csv(TABLES / "absorption.csv", index=False)

    print(f"Results written to {OUT / 'results.json'}")
    print(f"Cross-section specs: {len(regressions)}, panel specs: {len(panel_out)}, robustness: {len(robustness)}")
    return results


if __name__ == "__main__":
    main()
