"""Build the municipal panel and the 2024 cross-section.

Inputs (data/raw):
    ua_69330.csv                  INE Urban Indicators, long format
    dpop_29005.csv                INE Padrón, long format
    ua_municipality_codes.csv     name -> 5-digit code lookup
    siu/clases_suelo_mun.xlsx     municipal land-class shares
    siu/areas_desarrollo_mun.xlsx development areas, planned/pending dwellings
    siu/plan_mun.xlsx             planning instruments (not used in the baseline)
    serpavi_2011_2024.xlsx        SERPAVI municipal rents, used as an independent
                                  outcome source for the rent null

Outputs:
    data/processed/panel.csv
    data/processed/cross_section.csv
    outputs/coverage.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from config import MANUAL_CODE, PROC, PROVINCES, RAW, SIU, UA_INDICATORS, OUT

PANEL_YEARS = range(2010, 2026)
CS_YEAR = 2024


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_ine_number(s: pd.Series) -> pd.Series:
    """Spanish number format: 1.234.567,8 -> 1234567.8; '' -> NaN."""
    return pd.to_numeric(
        s.astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace({"": np.nan, "nan": np.nan, "None": np.nan}),
        errors="coerce",
    )


def normalise(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def token_key(s: str) -> str:
    """Order-insensitive name key, ignoring leading articles.

    'Palmas de Gran Canaria, Las' and 'Las Palmas de Gran Canaria' collide on
    purpose. Keys are only used when unique within the Padrón.
    """
    tokens = normalise(s).split()
    articles = {"LA", "EL", "LOS", "LAS"}
    return " ".join(sorted(t for t in tokens if t not in articles))


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_ua_codes(dpop: pd.DataFrame) -> dict[str, str]:
    codes = pd.read_csv(RAW / "ua_municipality_codes.csv", dtype=str)
    codes = codes.drop_duplicates()

    # Padrón names for 2025, with a uniqueness check on the token key.
    d25 = (
        dpop[dpop["year"] == 2025][["code", "name"]]
        .drop_duplicates()
        .assign(key=lambda d: d["name"].map(token_key))
    )
    counts = d25["key"].value_counts()
    unique = d25[d25["key"].isin(counts[counts == 1].index)]
    lookup = dict(zip(unique["key"], unique["code"]))

    def resolve(row):
        if re.fullmatch(r"\d{5}", row["tempus_code"] or ""):
            return row["tempus_code"]
        return lookup.get(token_key(row["name"])) or MANUAL_CODE.get(row["name"])

    codes["code"] = codes.apply(resolve, axis=1)
    missing = codes[codes["code"].isna()]
    if len(missing):
        raise ValueError(f"Unmapped INE municipality names: {missing['name'].tolist()}")
    return dict(zip(codes["name"], codes["code"]))


def load_ua(code_map: dict[str, str]) -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_csv(RAW / "ua_69330.csv", sep=";", encoding="utf-8", dtype=str)
    df.columns = ["national", "municipality", "indicator", "year", "value"]
    df = df[df["municipality"].notna()].copy()
    df["year"] = df["year"].astype(int)
    df["value"] = parse_ine_number(df["value"])
    df["variable"] = df["indicator"].map(UA_INDICATORS)
    dropped = sorted(df.loc[df["variable"].isna(), "indicator"].unique().tolist())
    df = df[df["variable"].notna()].copy()
    wide = (
        df.pivot_table(index=["municipality", "year"], columns="variable", values="value", aggfunc="first")
        .reset_index()
        .rename_axis(columns=None)
    )
    wide["code"] = wide["municipality"].map(code_map)
    if wide["code"].isna().any():
        raise ValueError("UA municipalities without a code after mapping")
    wide = wide.rename(columns={"municipality": "municipality_name"})
    return wide, dropped


def load_population() -> pd.DataFrame:
    df = pd.read_csv(RAW / "dpop_29005.csv", sep=";", encoding="utf-8", dtype=str)
    df.columns = ["municipality", "sex", "year", "value"]
    df["code"] = df["municipality"].str[:5]
    df["name"] = df["municipality"].str[6:]
    df["year"] = df["year"].astype(int)
    df["value"] = parse_ine_number(df["value"])
    return df


def load_serpavi() -> pd.DataFrame:
    """SERPAVI municipal rents for 2024 (tax-source statistic).

    ``ALQM2_LV_M_VC_24`` is the median monthly rent per m2 of collective
    residential buildings; ``BI_ALVHEPCO_TVC_24`` is the number of dwellings
    behind it.  This is an independent outcome from INE table 69330, which is
    built from a different operation, so agreement between the two is a real
    cross-source check rather than a restatement.
    """
    path = RAW / "serpavi_2011_2024.xlsx"
    cols = {
        "CUMUN": "code",
        "BI_ALVHEPCO_TVC_24": "serpavi_n",
        "ALQM2_LV_M_VC_24": "rent_m2_serpavi",
        "ALQM2_LV_25_VC_24": "serpavi_p25",
        "ALQM2_LV_75_VC_24": "serpavi_p75",
        "ALQTBID12_M_VC_24": "serpavi_rent_month",
        "SLVM2_M_VC_24": "serpavi_m2",
    }
    s = pd.read_excel(path, sheet_name="Municipios", usecols=list(cols), dtype={"CUMUN": str})
    s = s.rename(columns=cols)
    s["code"] = s["code"].str.zfill(5)
    if s["code"].duplicated().any():
        raise ValueError("SERPAVI municipality sheet has duplicate CUMUN codes")
    return s


def load_siu() -> pd.DataFrame:
    classes = pd.read_excel(SIU / "clases_suelo_mun.xlsx")
    areas = pd.read_excel(SIU / "areas_desarrollo_mun.xlsx")

    for df in (classes, areas):
        df["code"] = df["ProvINE"].astype(str).str.zfill(5)

    # The land-class shares are percentages of municipal area. They sum to 100
    # once the overlapping "areas de desarrollo" aggregate is excluded:
    # MunPrADes == MunPrSuNoC + MunPrSuzDe (checked in tests).
    s = classes.merge(
        areas.drop(columns=["DenoMun", "Planeamiento", "Fuente", "FechaAct"]),
        on="code",
        how="left",
        suffixes=("", "_areas"),
        validate="one_to_one",
    )

    s["municipality_name_siu"] = s["DenoMun"]
    s["mun_area_km2"] = s["MunTotSue"]

    s["share_urban_consolidated"] = s["MunPrSuCon"] / 100
    s["share_development_areas"] = s["MunPrADes"] / 100
    s["share_urban_nonconsolidated"] = s["MunPrSuNoC"] / 100
    s["share_urbanizable_delimited"] = s["MunPrSuzDe"] / 100
    s["share_urbanizable_undelimited"] = s["MunPrSuzNd"] / 100
    s["share_nonurbanizable"] = s["MunPrSnUzb"] / 100
    s["share_other"] = s["MunPrOtr"] / 100

    s["dev_area_m2"] = s["munsupadgr"]
    s["dev_area_ha"] = s["munsupadgr"] / 1e4
    s["planned_dwellings"] = s["munnumviv"]
    s["pending_dwellings"] = s["munnvivpnd"]
    s["pending_share"] = np.where(
        s["planned_dwellings"] > 0, s["pending_dwellings"] / s["planned_dwellings"], np.nan
    )
    s["pending_share"] = s["pending_share"].clip(0, 1)
    s["delivery_rate"] = 1 - s["pending_share"]
    s["unstarted_share"] = s["munpradsnu"] / 100
    s["planned_density_dwellings_ha"] = s["dens_viv"]
    s["imagery_year"] = pd.to_numeric(s["fechaimafo"], errors="coerce")

    # Plan year: the year in the instrument label ("Plan General (2023)").
    extracted = s["Planeamiento"].astype(str).str.extract(r"\((\d{4})\)")[0]
    s["plan_year"] = pd.to_numeric(extracted, errors="coerce")
    s["siu_update_year"] = pd.to_datetime(s["FechaAct"], dayfirst=True, errors="coerce").dt.year
    s["plan_year"] = s["plan_year"].fillna(s["siu_update_year"])
    s["plan_age"] = 2025 - s["plan_year"]
    s["plan_type"] = s["Planeamiento"].astype(str).str.split("(").str[0].str.strip()

    keep = [
        "code", "municipality_name_siu", "Planeamiento", "plan_type", "plan_year",
        "plan_age", "siu_update_year", "imagery_year", "mun_area_km2",
        "share_urban_consolidated", "share_development_areas",
        "share_urban_nonconsolidated", "share_urbanizable_delimited",
        "share_urbanizable_undelimited", "share_nonurbanizable", "share_other",
        "dev_area_m2", "dev_area_ha", "planned_dwellings", "pending_dwellings",
        "pending_share", "delivery_rate", "unstarted_share",
        "planned_density_dwellings_ha",
    ]
    return s[keep].copy()


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    pop = load_population()
    code_map = load_ua_codes(pop)
    ua, ua_dropped = load_ua(code_map)
    siu = load_siu()
    serpavi = load_serpavi()

    pop_total = (
        pop[pop["sex"] == "Total"][["code", "year", "value"]]
        .rename(columns={"value": "population"})
        .drop_duplicates(["code", "year"])
    )

    panel = ua.merge(pop_total, on=["code", "year"], how="left")
    panel["province_code"] = panel["code"].str[:2]
    panel["province"] = panel["province_code"].map(PROVINCES)
    panel = panel[panel["year"].isin(PANEL_YEARS)].sort_values(["code", "year"])

    # Cross-section: latest year with rents.
    cs = panel[panel["year"] == CS_YEAR].merge(siu, on="code", how="inner")
    cs = cs.merge(serpavi, on="code", how="left")

    p15 = pop_total[pop_total["year"] == 2015][["code", "population"]].rename(
        columns={"population": "population_2015"}
    )
    cs = cs.merge(p15, on="code", how="left")

    cs["log_population"] = np.log(cs["population"].where(cs["population"] > 0))
    cs["log_stock"] = np.log(cs["stock_catastro"].where(cs["stock_catastro"] > 0))
    cs["population_growth_15_24"] = np.log(cs["population"] / cs["population_2015"])
    cs["density_pop_km2"] = cs["population"] / cs["mun_area_km2"]
    cs["log_density"] = np.log(cs["density_pop_km2"].where(cs["density_pop_km2"] > 0))

    cs["planned_per_1000_stock"] = np.where(
        cs["stock_catastro"] > 0, cs["planned_dwellings"] / cs["stock_catastro"] * 1000, np.nan
    )
    cs["pending_per_1000_stock"] = np.where(
        cs["stock_catastro"] > 0, cs["pending_dwellings"] / cs["stock_catastro"] * 1000, np.nan
    )
    cs["dev_area_m2_per_capita"] = np.where(
        cs["population"] > 0, cs["dev_area_m2"] / cs["population"], np.nan
    )
    cs["rent_to_price"] = cs["rent_m2_year"] / cs["price_m2"]
    cs["log_rent"] = np.log(cs["rent_m2_year"].where(cs["rent_m2_year"] > 0))
    cs["log_rent_serpavi"] = np.log(cs["rent_m2_serpavi"].where(cs["rent_m2_serpavi"] > 0))
    cs["log_price"] = np.log(cs["price_m2"].where(cs["price_m2"] > 0))
    cs["log_rent_to_price"] = np.log(cs["rent_to_price"].where(cs["rent_to_price"] > 0))

    coverage = {
        "siu_municipalities": int(siu["code"].nunique()),
        "ua_municipalities": int(ua["code"].nunique()),
        "ua_matched_to_siu": int(cs["code"].nunique()),
        "ua_match_rate": float(cs["code"].nunique() / ua["code"].nunique()),
        "cross_section_n": int(len(cs)),
        "rent_2024_nonmissing": int(cs["rent_m2_year"].notna().sum()),
        "serpavi_municipalities": int(serpavi["code"].nunique()),
        "serpavi_matched": int(cs["rent_m2_serpavi"].notna().sum()),
        "serpavi_matched_n_ge_30": int((cs["serpavi_n"] >= 30).sum()),
        "serpavi_rent_nonmissing": int(cs["rent_m2_serpavi"].notna().sum()),
        "price_2024_nonmissing": int(cs["price_m2"].notna().sum()),
        "stock_2024_nonmissing": int(cs["stock_catastro"].notna().sum()),
        "planned_dwellings_nonmissing": int(cs["planned_dwellings"].notna().sum()),
        "pending_dwellings_nonmissing": int(cs["pending_dwellings"].notna().sum()),
        "pending_share_nonmissing": int(cs["pending_share"].notna().sum()),
        "unstarted_share_nonmissing": int(cs["unstarted_share"].notna().sum()),
        "years_panel": [int(panel["year"].min()), int(panel["year"].max())],
        "panel_rows": int(len(panel)),
        "panel_municipalities": int(panel["code"].nunique()),
        "ua_indicators_dropped": ua_dropped,
        "notes": {
            "land_shares": "Percentages of municipal area. Sum to 100 excluding share_development_areas, which overlaps urban_nonconsolidated + urbanizable_delimited.",
            "mun_area_km2": "SIU MunTotSue, municipal area in km2 (checked against known municipal areas).",
            "pending_share": "pending_dwellings / planned_dwellings. A stock of plan capacity, not a delay measure.",
            "rents": "INE Urban Indicators table 69330, annual rent in EUR/m2.",
            "serpavi": "MIVAU SERPAVI 2011-2024, Municipios sheet, 2024 median monthly rent per m2 of collective residential buildings. Tax-source statistic (Modelo 100), independent of INE 69330; excludes Navarra and the Basque Country.",
        },
    }

    panel.to_csv(PROC / "panel.csv", index=False, encoding="utf-8")
    cs.to_csv(PROC / "cross_section.csv", index=False, encoding="utf-8")
    (OUT / "coverage.json").write_text(json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Panel:        {len(panel):,} rows, {panel['code'].nunique():,} municipalities, {panel['year'].min()}-{panel['year'].max()}")
    print(f"Cross-section:{len(cs):,} municipalities ({cs['rent_m2_year'].notna().sum():,} with rent)")
    print(f"SIU match:    {cs['code'].nunique():,}/{ua['code'].nunique():,} UA municipalities")
    print(f"Coverage:     {OUT / 'coverage.json'}")
    return panel, cs, coverage


if __name__ == "__main__":
    build()
