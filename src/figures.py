"""Figures for the housing / land-classification project."""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from matplotlib.ticker import FuncFormatter

from config import FIGURES, OUT, PROC, PROVINCES

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


def thousands(x, _pos=None):
    return f"{x/1000:,.0f}k"


def fig_pipeline_gap(cs: pd.DataFrame, results: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1))

    ax = axes[0]
    s = cs["pending_share"].dropna()
    ax.hist(s, bins=np.arange(0, 1.02, 0.05), color=NAVY, alpha=0.85, edgecolor="white")
    ax.axvline(s.median(), color=RUST, lw=1.8, label=f"Median municipality: {s.median():.0%}")
    ax.axvline(results["pipeline"]["aggregate_pending_share"], color=GRAY, lw=1.8, ls="--",
               label=f"Aggregate: {results['pipeline']['aggregate_pending_share']:.0%}")
    ax.set_xlabel("Share of planned dwellings not yet materialised")
    ax.set_ylabel("Municipalities")
    ax.set_title("A. The unbuilt pipeline is the norm")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    ax = axes[1]
    prov = pd.DataFrame(results["provinces"]).nlargest(15, "planned_dwellings").iloc[::-1]
    built = prov["planned_dwellings"] - prov["pending_dwellings"]
    ax.barh(prov["province"], built / 1000, color=NAVY, label="Materialised")
    ax.barh(prov["province"], prov["pending_dwellings"] / 1000, left=built / 1000, color=RUST, label="Pending")
    ax.set_xlabel("Dwellings planned in development areas (thousands)")
    ax.set_title("B. Planned capacity by province, top 15")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.grid(axis="y", visible=False)

    fig.tight_layout()
    fig.savefig(FIGURES / "fig1_pipeline_gap.png", bbox_inches="tight")
    plt.close(fig)


def fig_capacity_and_demand(cs: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    d = cs.dropna(subset=["planned_per_1000_stock", "population_growth_15_24"])
    ax.scatter(
        d["population_growth_15_24"] * 100,
        d["planned_per_1000_stock"],
        s=18,
        color=NAVY,
        alpha=0.45,
        edgecolor="white",
        linewidth=0.3,
    )
    # medians by tercile
    d = d.copy()
    d["tercile"] = pd.qcut(d["population_growth_15_24"], 3, labels=False)
    med = d.groupby("tercile")[["population_growth_15_24", "planned_per_1000_stock"]].median()
    ax.plot(med["population_growth_15_24"] * 100, med["planned_per_1000_stock"],
            color=RUST, marker="o", lw=2.2, ms=6, label="Tercile median")
    ax.set_yscale("log")
    ax.set_xlabel("Population growth 2015–2024 (%)")
    ax.set_ylabel("Planned dwellings per 1,000 existing")
    ax.set_title("Planned capacity is only weakly related to demand growth")
    ax.text(
        0.03, 0.95,
        f"r = {d['planned_per_1000_stock'].corr(d['population_growth_15_24']):.2f}",
        transform=ax.transAxes, va="top", fontsize=9, color=RUST,
    )
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig2_capacity_vs_demand.png", bbox_inches="tight")
    plt.close(fig)


def fig_coefficients(results: dict) -> None:
    regs = pd.DataFrame(results["regressions"])
    d = regs[regs["outcome"] == "log_rent"].copy()
    label_map = {
        "share_nonurbanizable": "Non-urbanizable land (%)",
        "share_development_areas": "Development land (%)",
        "planned_per_1000_stock": "Planned dwellings / stock",
        "pending_share": "Pending share",
        "unstarted_share": "Unstarted development land",
    }
    d["label"] = d["measure"].map(label_map)
    order = ["Non-urbanizable land (%)", "Development land (%)", "Planned dwellings / stock",
             "Pending share", "Unstarted development land"]
    d["label"] = pd.Categorical(d["label"], categories=order, ordered=True)
    d = d.sort_values(["controls", "label"])

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    y = np.arange(len(order))
    for offset, (ctrl, color, marker) in zip(
        (-0.16, 0.16),
        [("basic", GRAY, "o"), ("urban", NAVY, "s")],
    ):
        sub = d[d["controls"] == ctrl].set_index("label").reindex(order)
        ax.errorbar(
            sub["coef_per_sd"], y + offset,
            xerr=[sub["coef_per_sd"] - sub["ci_lo"], sub["ci_hi"] - sub["coef_per_sd"]],
            fmt=marker, color=color, ecolor=color, elinewidth=1.4, capsize=3, ms=5,
            label="Province FE + basic controls" if ctrl == "basic" else "Province FE + urban controls",
        )
    ax.axvline(0, color="#333333", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(order)
    ax.set_xlabel("Association with log rent (per 1 SD of the measure)")
    ax.set_title("Rent associations are null or the wrong sign")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig3_rent_coefficients.png", bbox_inches="tight")
    plt.close(fig)


def fig_added_variable(cs: pd.DataFrame) -> None:
    controls = ["log_population", "log_stock", "population_growth_15_24", "log_density", "share_urban_consolidated"]
    d = cs.dropna(subset=["log_rent", "share_nonurbanizable"] + controls).copy()
    f = " + ".join(controls) + " + C(province_code)"
    ry = smf.ols(f"log_rent ~ {f}", data=d).fit().resid
    rx = smf.ols(f"share_nonurbanizable ~ {f}", data=d).fit().resid
    d["res_rent"] = ry
    d["res_land"] = rx
    d["bin"] = pd.qcut(d["res_land"], 20, duplicates="drop")
    b = d.groupby("bin", observed=True).agg(x=("res_land", "mean"), y=("res_rent", "mean"))

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0))
    ax = axes[0]
    ax.scatter(d["share_nonurbanizable"] * 100, d["log_rent"], s=14, color=NAVY, alpha=0.4,
               edgecolor="white", linewidth=0.25)
    z = np.polyfit(d["share_nonurbanizable"] * 100, d["log_rent"], 1)
    xs = np.linspace((d["share_nonurbanizable"] * 100).min(), (d["share_nonurbanizable"] * 100).max(), 50)
    ax.plot(xs, np.polyval(z, xs), color=RUST, lw=2)
    ax.set_xlabel("Non-urbanizable land (% of municipal area)")
    ax.set_ylabel("Log annual rent (€/m²)")
    ax.set_title("A. Raw: more protected land, lower rents")
    ax.text(0.03, 0.95, f"r = {d['share_nonurbanizable'].corr(d['log_rent']):.2f}",
            transform=ax.transAxes, va="top", fontsize=9, color=RUST)

    ax = axes[1]
    ax.scatter(d["res_land"], d["res_rent"], s=14, color=GRAY, alpha=0.35, edgecolor="none")
    ax.plot(b["x"], b["y"], color=NAVY, marker="o", lw=2, ms=5)
    ax.axhline(0, color="#333333", lw=0.8)
    ax.axvline(0, color="#333333", lw=0.8)
    ax.set_xlabel("Non-urbanizable land, residualised")
    ax.set_ylabel("Log rent, residualised")
    ax.set_title("B. After province FE and urban controls: flat")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig4_raw_vs_adjusted.png", bbox_inches="tight")
    plt.close(fig)


def fig_top_pending(cs: pd.DataFrame) -> None:
    d = cs.nlargest(15, "pending_dwellings").sort_values("pending_dwellings")
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    pending_k = d["pending_dwellings"] / 1000
    built_k = (d["planned_dwellings"] - d["pending_dwellings"]) / 1000
    total_k = pending_k + built_k
    ax.barh(d["municipality_name"], pending_k, color=RUST, alpha=0.92, label="Pending")
    ax.barh(d["municipality_name"], built_k, left=pending_k, color=NAVY, label="Materialised")
    ax.set_xlabel("Dwellings planned in development areas (thousands)")
    ax.set_title("Where the paper housing is concentrated")
    ax.set_xlim(0, total_k.max() * 1.22)
    for i, (_, row) in enumerate(d.iterrows()):
        ax.text(total_k.iloc[i] + 2, i, f"{row['pending_share']:.0%} pending",
                va="center", fontsize=7.5, color="#333333")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig5_top_pending.png", bbox_inches="tight")
    plt.close(fig)


def fig_growth_terciles(results: dict) -> None:
    t = pd.DataFrame(results["terciles"])
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.7))
    labels = ["Declining", "Moderate", "Fast-growing"]
    ax = axes[0]
    ax.bar(labels, t["planned_per_1000_stock"], color=NAVY)
    ax.set_ylabel("Planned dwellings per 1,000 existing")
    ax.set_title("A. Fast-growing places do plan more")
    ax = axes[1]
    ax.bar(labels, t["pending_share"], color=RUST)
    ax.set_ylabel("Median pending share")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.set_title("B. But the gap barely moves")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig6_growth_terciles.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    cs = pd.read_csv(PROC / "cross_section.csv", dtype={"code": str, "province_code": str})
    results = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    fig_pipeline_gap(cs, results)
    fig_capacity_and_demand(cs)
    fig_coefficients(results)
    fig_added_variable(cs)
    fig_top_pending(cs)
    fig_growth_terciles(results)
    print(f"Figures written to {FIGURES}")


if __name__ == "__main__":
    main()
