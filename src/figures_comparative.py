"""Figures for the comparative chapter.

Three figures, all descriptive:

- fig8: price-to-income, Spain against peers over time and against the OECD
  distribution of 2015-to-latest changes.
- fig9: building permits per 1,000 inhabitants, peer dumbbell and Spain's own
  annual series since 2005.
- fig10: city price-to-rent, country distribution and the Spanish city scatter.

The figures read the tables written by `comparative.py`; the two series that are
not in those tables (the OECD cross-country median and Spain's annual permits)
are rebuilt from the cached raw files with the same parsers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from comparative import oecd_panel, permits_panel, eurostat_tidy
from config import COUNTRY_NAMES, FIGURES, PEER_COUNTRIES, RAW, TABLES

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#4a4a4a",
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "#e6e6e6",
    "grid.linewidth": 0.6,
    "figure.facecolor": "white",
})

NAVY = "#1f3a5f"
RUST = "#c8553d"
GRAY = "#8a8f98"
SAND = "#e8e6e1"
INK = "#333333"


def _short(iso3: str) -> str:
    return COUNTRY_NAMES.get(iso3, iso3)


def fig_price_to_income(oecd: pd.DataFrame, countries: pd.DataFrame) -> None:
    fig, axes = plt.subplots(
        1, 2, figsize=(11.2, 4.6), gridspec_kw={"width_ratios": [1.15, 1.0]}
    )

    # ---------------------------------------------------------------- panel A
    ax = axes[0]
    ydh = oecd[oecd["MEASURE"] == "HPI_YDH"]
    median = ydh.groupby("year")["OBS_VALUE"].median().sort_index()
    peers = ["ESP", "PRT", "DEU", "FRA", "ITA", "NLD"]
    colors = {
        "ESP": RUST,
        "PRT": "#d98b7b",
        "DEU": "#4f6076",
        "FRA": "#7d8b9e",
        "ITA": "#9aa6b4",
        "NLD": "#b8c0ca",
    }
    for iso3 in peers:
        series = ydh[ydh["REF_AREA"] == iso3].set_index("year")["OBS_VALUE"].sort_index()
        series = series.loc[series.index >= 2000]
        ax.plot(
            series.index,
            series.values,
            color=colors[iso3],
            lw=2.6 if iso3 == "ESP" else 1.2,
            label=_short(iso3),
            zorder=4 if iso3 == "ESP" else 2,
        )
    ax.plot(
        median.loc[median.index >= 2000].index,
        median.loc[median.index >= 2000].values,
        color=NAVY,
        lw=1.5,
        ls="--",
        label="Country median",
        zorder=3,
    )
    ax.axhline(100, color=GRAY, lw=0.8, ls=":")
    ax.set_xlim(2000, 2025)
    ax.set_ylabel("Price-to-income index (2015 = 100)")
    ax.set_title("A. The ratio rose faster in Spain than in most peers")
    ax.legend(frameon=False, fontsize=7.5, ncol=2, loc="upper left")

    # ---------------------------------------------------------------- panel B
    ax = axes[1]
    d = countries[
        countries["iso3"].isin(PEER_COUNTRIES)
        & countries["price_to_income_chg_2015_pct"].notna()
    ].sort_values("price_to_income_chg_2015_pct")
    y = np.arange(len(d))
    bar_colors = [RUST if iso3 == "ESP" else NAVY for iso3 in d["iso3"]]
    ax.barh(y, d["price_to_income_chg_2015_pct"], color=bar_colors, height=0.66)
    ax.set_yticks(y)
    ax.set_yticklabels([_short(i) for i in d["iso3"]], fontsize=7.5)
    ax.axvline(0, color=INK, lw=0.8)
    for yi, value in zip(y, d["price_to_income_chg_2015_pct"]):
        ax.text(
            value + (1.2 if value >= 0 else -1.2),
            yi,
            f"{value:+.0f}",
            va="center",
            ha="left" if value >= 0 else "right",
            fontsize=6.5,
            color=INK,
        )
    ax.set_xlabel("Change 2015 to latest (%)")
    ax.set_title("B. Spain is high, but not an outlier")

    spain = countries[countries["iso3"] == "ESP"].iloc[0]
    median_all = countries["price_to_income_chg_2015_pct"].median()
    n_all = int(countries["price_to_income_chg_2015_pct"].notna().sum())
    ax.text(
        0.98,
        0.03,
        (
            f"Spain {spain['price_to_income_chg_2015_pct']:+.1f}% "
            f"(rank {int(spain['price_to_income_rank_2015'])} of {n_all})\n"
            f"Median, {n_all}-country sample {median_all:+.1f}%"
        ),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.5,
        color=INK,
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#cccccc", lw=0.6),
    )
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.text(
        0.01, -0.01,
        "Panel A median: countries with data each year (25 in 2000, 36 in 2025).",
        fontsize=7, color=GRAY, ha="left", va="top",
    )
    fig.savefig(FIGURES / "fig8_price_to_income.png", bbox_inches="tight")
    plt.close(fig)


def fig_permits(countries: pd.DataFrame, permits: pd.DataFrame) -> None:
    fig, axes = plt.subplots(
        1, 2, figsize=(11.2, 4.6), gridspec_kw={"width_ratios": [1.0, 1.15]}
    )

    # ---------------------------------------------------------------- panel A
    ax = axes[0]
    d = countries[
        countries["iso3"].isin(PEER_COUNTRIES)
        & countries["permits_per_1000_2015_2019"].notna()
        & countries["permits_per_1000_2021_2024"].notna()
    ].sort_values("permits_per_1000_2021_2024")
    y = np.arange(len(d))
    for yi, (_, row) in zip(y, d.iterrows()):
        ax.plot(
            [row["permits_per_1000_2015_2019"], row["permits_per_1000_2021_2024"]],
            [yi, yi],
            color="#c9ced6",
            lw=1.4,
            zorder=1,
        )
    ax.scatter(
        d["permits_per_1000_2015_2019"], y, s=26, color=GRAY, zorder=3,
        label="2015-2019",
    )
    right_colors = [RUST if iso3 == "ESP" else NAVY for iso3 in d["iso3"]]
    ax.scatter(d["permits_per_1000_2021_2024"], y, s=34, color=right_colors, zorder=4,
               label="2021-2024")
    ax.set_yticks(y)
    ax.set_yticklabels([_short(i) for i in d["iso3"]], fontsize=7.5)
    for tick, iso3 in zip(ax.get_yticklabels(), d["iso3"]):
        if iso3 == "ESP":
            tick.set_color(RUST)
            tick.set_fontweight("bold")
    ax.set_xlabel("Dwellings permitted per 1,000 inhabitants")
    ax.set_title("A. Spain builds less than most European peers")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    ax.grid(axis="y", visible=False)

    # ---------------------------------------------------------------- panel B
    ax = axes[1]
    es = permits[(permits["geo"] == "ES") & (permits["year"] >= 2005)].sort_values("year")
    ax.plot(es["year"], es["permits_per_1000"], color=NAVY, lw=1.8, marker="o", ms=3.5)
    ax.axhline(
        countries.loc[countries["iso3"] == "ESP", "permits_per_1000_2021_2024"].iloc[0],
        color=RUST, lw=1.0, ls="--",
    )
    ax.text(
        2005.3,
        countries.loc[countries["iso3"] == "ESP", "permits_per_1000_2021_2024"].iloc[0] + 0.45,
        "2021-2024 average 2.64",
        fontsize=7.5,
        color=RUST,
    )
    europe = countries["permits_per_1000_2021_2024"].median()
    ax.axhline(europe, color=GRAY, lw=1.0, ls=":")
    ax.text(2005.3, europe + 0.45, f"Europe 2021-2024 median {europe:.2f}",
            fontsize=7.5, color=GRAY)

    peak_year = int(es.loc[es["permits_per_1000"].idxmax(), "year"])
    peak_value = float(es["permits_per_1000"].max())
    ax.annotate(
        f"{peak_value:.1f} in {peak_year}",
        xy=(peak_year, peak_value),
        xytext=(peak_year + 1.5, peak_value + 0.7),
        fontsize=8,
        color=INK,
        arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8),
    )
    last = es.iloc[-1]
    ax.annotate(
        f"{last['permits_per_1000']:.1f} in {int(last['year'])}",
        xy=(last["year"], last["permits_per_1000"]),
        xytext=(last["year"] - 5.5, last["permits_per_1000"] + 1.0),
        fontsize=8,
        color=INK,
        arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8),
    )
    ax.set_xlim(2005, 2024.5)
    ax.set_ylim(0, 18.5)
    ax.set_xticks([2005, 2008, 2011, 2014, 2017, 2020, 2023])
    ax.set_ylabel("Dwellings permitted per 1,000 inhabitants")
    ax.set_xlabel("Year")
    ax.set_title("B. Spain's own boom, crash and partial recovery")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig9_permits.png", bbox_inches="tight")
    plt.close(fig)


def fig_city_price_to_rent(cities: pd.DataFrame) -> None:
    fig, axes = plt.subplots(
        1, 2, figsize=(11.2, 4.6), gridspec_kw={"width_ratios": [1.0, 1.15]}
    )

    # ---------------------------------------------------------------- panel A
    ax = axes[0]
    comp = cities[cities["comparable"]].copy()
    order = (
        comp.groupby("country")["price_to_rent"].median().sort_values().index.tolist()
    )
    data = [comp.loc[comp["country"] == c, "price_to_rent"].values for c in order]
    positions = np.arange(len(order))
    box = ax.boxplot(
        data,
        positions=positions,
        widths=0.52,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color=INK, lw=1.2),
        whiskerprops=dict(color=GRAY, lw=0.9),
        capprops=dict(color=GRAY, lw=0.9),
        boxprops=dict(lw=0.9),
    )
    for patch, country in zip(box["boxes"], order):
        if country == "ES":
            patch.set_facecolor("#f0c9c0")
            patch.set_edgecolor(RUST)
        else:
            patch.set_facecolor(SAND)
            patch.set_edgecolor(GRAY)
    rng = np.random.default_rng(0)
    for position, country in zip(positions, order):
        values = comp.loc[comp["country"] == country, "price_to_rent"].values
        jitter = rng.uniform(-0.16, 0.16, size=len(values))
        color = RUST if country == "ES" else GRAY
        ax.scatter(
            position + jitter, values, s=7, color=color, alpha=0.45, zorder=3,
            linewidths=0,
        )
        ax.text(
            position,
            np.percentile(values, 75) + (3.2 if country == "ES" else 2.2),
            f"{np.median(values):.1f}",
            ha="center",
            fontsize=7.5,
            color=RUST if country == "ES" else INK,
            fontweight="bold" if country == "ES" else "normal",
        )
    ax.set_xticks(positions)
    names = comp.groupby("country")["country_name"].first().to_dict()
    ax.set_xticklabels(
        [f"{names[c]}\n(n={int((comp['country'] == c).sum())})" for c in order],
        fontsize=7.5,
    )
    ax.set_ylabel("Price-to-rent (years of gross rent)")
    ax.set_ylim(8, 55)
    ax.set_title("A. Spanish cities are not the priciest relative to rent")
    ax.grid(axis="x", visible=False)
    ax.text(
        0.02, 0.97,
        "Latvia excluded (internally inconsistent rent units)",
        transform=ax.transAxes, fontsize=7, color=GRAY, va="top",
    )

    # ---------------------------------------------------------------- panel B
    ax = axes[1]
    es = cities[cities["country"] == "ES"].copy()
    size = 16 + 70 * (es["population"] / es["population"].max()) ** 0.5
    ax.scatter(
        es["rent_m2_annual"], es["price_m2"], s=size, color=GRAY, alpha=0.45,
        linewidths=0, zorder=2,
    )
    labelled = [
        "Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga",
        "Palma de Mallorca", "Eivissa",
    ]
    offsets = {
        "Madrid": (-45, 8),
        "Barcelona": (6, -14),
        "Valencia": (5, -12),
        "Sevilla": (5, -14),
        "Málaga": (5, 7),
        "Palma de Mallorca": (-78, 2),
        "Eivissa": (-42, 10),
    }
    for name in labelled:
        row = es[es["city_name_clean"] == name]
        if row.empty:
            continue
        row = row.iloc[0]
        ax.scatter(row["rent_m2_annual"], row["price_m2"], s=34, color=RUST, zorder=4)
        dx, dy = offsets[name]
        ax.annotate(
            name,
            xy=(row["rent_m2_annual"], row["price_m2"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=7,
            color=RUST,
        )
    x = np.linspace(45, 170, 50)
    for years, label in [(10, "10 years"), (16.6, "Spain median 16.6"), (25, "25 years")]:
        ax.plot(x, x * years, color="#cccccc", lw=0.9, ls="--", zorder=1)
        ax.text(168, 168 * years, label, fontsize=6.5, color=GRAY, ha="right", va="bottom")
    ax.set_xlim(45, 172)
    ax.set_ylim(400, 4700)
    ax.set_xlabel("Annual rent (EUR per m2)")
    ax.set_ylabel("Purchase price (EUR per m2)")
    ax.set_title("B. Spanish cities: price against rent")
    ax.text(
        0.02, 0.97,
        "Dashed lines: price-to-rent of 10, 16.6 and 25 years",
        transform=ax.transAxes, fontsize=7, color=GRAY, va="top",
    )
    fig.tight_layout()
    fig.text(
        0.01, -0.01,
        "Latest year per city: Spain 2023, Germany 2022, Portugal 2024, Lithuania 2025. "
        "Municipal boundaries only: 207 cities, 5 countries, Spain 16.06 years (3rd of 5).",
        fontsize=7, color=GRAY, ha="left", va="top",
    )
    fig.savefig(FIGURES / "fig10_city_price_to_rent.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    oecd = oecd_panel(RAW / "oecd_house_prices.csv")
    permits_raw = eurostat_tidy(RAW / "eurostat_permits.json")
    population = eurostat_tidy(RAW / "eurostat_population.json")
    permits = permits_panel(permits_raw, population)
    countries = pd.read_csv(TABLES / "comparative_countries.csv")
    cities = pd.read_csv(TABLES / "comparative_cities.csv")

    fig_price_to_income(oecd, countries)
    fig_permits(countries, permits)
    fig_city_price_to_rent(cities)
    print(f"Comparative figures written to {FIGURES}")


if __name__ == "__main__":
    main()
