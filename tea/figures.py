"""Figures for the Stage 1 report. python -m tea.figures"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .model import economics
from .routes import build_routes, aggregation_route
from .run import capacity_sweep, tornado, OUT
from .params import GLYCERINE_HISTORY, CENTS_LB_TO_USD_T, CRUDE_TPY

plt.rcParams.update({
    "figure.dpi": 150, "font.size": 9, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

INK, ACCENT, WARN, MUTED = "#1b2a41", "#2f6f4e", "#a33a2a", "#8a94a6"


def fig_capacity(path):
    df = capacity_sweep()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.0))

    ax1.axhline(0, color=INK, lw=1)
    ax1.plot(df["Crude fed (t/yr)"] / 1000, df["NPV ($M)"], color=ACCENT, lw=2.2)
    ax1.axvline(CRUDE_TPY / 1000, color=WARN, ls="--", lw=1.4)
    ax1.annotate("client's own\ncrude: 10 kt/yr", xy=(10, -6), xytext=(11.5, -7.5),
                 color=WARN, fontsize=8)

    from scipy.optimize import brentq
    from .routes import aggregation_route
    from .model import economics
    be = brentq(lambda c: economics(aggregation_route(c))["NPV_$"],
                10000.0, 200000.0, xtol=1.0) / 1000
    ax1.plot([be], [0], "o", color=INK, ms=7, zorder=5)
    ax1.annotate(f"minimum economic\nscale: {be:.1f} kt/yr", xy=(be, 0),
                 xytext=(be - 22, 8), fontsize=8, color=INK,
                 arrowprops=dict(arrowstyle="->", color=INK, lw=1))
    # The regional feedstock pool is the binding constraint, not the economics.
    ax1.axvline(42.0, color=ACCENT, ls=":", lw=1.5)
    ax1.text(42.6, ax1.get_ylim()[0] * 0.55,
             "entire PADD 1\ncrude pool: ~42 kt/yr", fontsize=8, color=ACCENT)
    ax1.fill_between(df["Crude fed (t/yr)"] / 1000, df["NPV ($M)"], 0,
                     where=df["NPV ($M)"] < 0, color=WARN, alpha=0.10)
    ax1.fill_between(df["Crude fed (t/yr)"] / 1000, df["NPV ($M)"], 0,
                     where=df["NPV ($M)"] >= 0, color=ACCENT, alpha=0.12)
    ax1.set_xlabel("Crude glycerol processed (thousand t/yr)")
    ax1.set_ylabel("NPV at 12% ($M)")
    ax1.set_title("Purification needs more crude than the region has",
                  loc="left", fontweight="bold")

    ax2.plot(df["Crude fed (t/yr)"] / 1000, df["Fixed opex ($/t crude)"],
             color=WARN, lw=2, label="Fixed opex")
    ax2.plot(df["Crude fed (t/yr)"] / 1000, df["Margin ($/t crude)"],
             color=ACCENT, lw=2, label="Gross margin")
    ax2.axvline(CRUDE_TPY / 1000, color=MUTED, ls="--", lw=1.2)
    ax2.set_xlabel("Crude glycerol processed (thousand t/yr)")
    ax2.set_ylabel("$ per tonne of crude fed")
    ax2.set_title("Fixed cost per tonne is what scale buys", loc="left",
                  fontweight="bold")
    ax2.legend(frameon=False)

    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fig_history(path):
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    labels = [h[1] for h in GLYCERINE_HISTORY]
    x = np.arange(len(labels))
    tech = np.array([h[3] for h in GLYCERINE_HISTORY]) * CENTS_LB_TO_USD_T
    crude = np.array([h[4] for h in GLYCERINE_HISTORY]) * CENTS_LB_TO_USD_T

    ax.fill_between(x, crude, tech, color=ACCENT, alpha=0.15,
                    label="Spread = the entire purification business")
    ax.plot(x, tech, "o-", color=INK, lw=2, label="Technical grade 99.5%")
    ax.plot(x, crude, "o-", color=WARN, lw=2, label="Crude 80%")
    for i in range(len(x)):
        ax.annotate(f"${tech[i]-crude[i]:,.0f}", xy=(x[i], (tech[i]+crude[i])/2),
                    ha="center", fontsize=8, color=ACCENT, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("$ per tonne")
    ax.set_title("The refined-to-crude spread has moved 2.8x in four years\n"
                 "Argus Glycerine, US Midwest", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fig_tornado(path):
    routes = {r.code: r for r in build_routes()}
    df = tornado(routes["E3"]).head(8).iloc[::-1]
    base = economics(routes["E3"])["NPV_$"] / 1e6

    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    y = np.arange(len(df))
    for i, (_, row) in enumerate(df.iterrows()):
        lo, hi = row["NPV at low ($M)"], row["NPV at high ($M)"]
        ax.barh(i, lo - base, left=base, height=0.62,
                color=WARN if lo < base else ACCENT, alpha=0.85)
        ax.barh(i, hi - base, left=base, height=0.62,
                color=ACCENT if hi > base else WARN, alpha=0.85)
    ax.axvline(base, color=INK, lw=1.6)
    ax.annotate(f"base case\n${base:.1f}M", xy=(base, len(df) - 0.3),
                xytext=(base + 6, len(df) - 0.75), fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(df["Variable"], fontsize=8)
    ax.set_xlabel("NPV at 12% ($M)")
    ax.set_title("What moves the answer - best build option (E3, 30 kt/yr)",
                 loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fig_ranking(path):
    routes = {r.code: r for r in build_routes()}
    codes = ["E3", "C2", "C1", "E1", "A1", "F1", "D1", "B1"]
    res = [(c, economics(routes[c])) for c in codes]
    res.sort(key=lambda t: t[1]["NPV_$"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.0), sharey=True)
    y = np.arange(len(res))
    names = [f"{c}  {e['name'][:38]}" for c, e in res]

    m = [e["margin_per_t_crude_$"] for _, e in res]
    ax1.barh(y, m, color=[ACCENT if v >= 0 else WARN for v in m], alpha=0.85)
    ax1.axvline(0, color=INK, lw=1.2)
    ax1.set_yticks(y); ax1.set_yticklabels(names, fontsize=8)
    ax1.set_xlabel("Gross margin ($/t crude fed)")
    ax1.set_title("The comparator the brief mandates...", loc="left",
                  fontweight="bold")

    n = [e["NPV_$"] / 1e6 for _, e in res]
    ax2.barh(y, n, color=[ACCENT if v >= 0 else WARN for v in n], alpha=0.85)
    ax2.axvline(0, color=INK, lw=1.2)
    ax2.set_xlabel("NPV at 12% ($M)")
    ax2.set_title("...and the one that decides", loc="left", fontweight="bold")

    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    fig_capacity(os.path.join(OUT, "fig1_capacity.png"))
    fig_history(os.path.join(OUT, "fig2_spread_history.png"))
    fig_tornado(os.path.join(OUT, "fig3_tornado.png"))
    fig_ranking(os.path.join(OUT, "fig4_ranking.png"))
    print("Figures written to", OUT)


if __name__ == "__main__":
    main()
