#!/usr/bin/env python3
"""Generate Manchester United Chapter 3 narrative charts.

This script combines:
- PCA outputs (PC1/PC2/PC3 and competitiveness index)
- league performance (points and league position)
- manager and tactical-era annotations

Outputs are saved under chapter3_competitiveness/manutd_story_charts.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FormatStrFormatter, LinearLocator, MaxNLocator

PCA_SCORES_PATH = Path("chapter3_competitiveness/competitiveness_pca_scores.csv")
LEAGUE_STATS_PATH = Path("all_stats.csv")
OUTPUT_DIR = Path("chapter3_competitiveness/manutd_story_charts")

TEAM_NAME = "Manchester Utd"

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.unicode_minus"] = False

STYLE_COLORS = sns.color_palette("Set2", n_colors=6)


def season_start_year(season: str) -> int:
    normalized = str(season).replace("-", "_")
    return int(normalized.split("_")[0])


def season_to_hyphen(season: str) -> str:
    return str(season).replace("_", "-")


def manager_for_year(year: int) -> str:
    if year == 2016:
        return "Mourinho"
    if year in (2017, 2018):
        return "Mourinho / Solskjaer"
    if year in (2019, 2020, 2021):
        return "Solskjaer / Rangnick"
    return "Ten Hag"


def tactical_era_for_year(year: int) -> str:
    if year in (2016, 2017):
        return "Low-risk transition + crossing"
    if year in (2018, 2019, 2020):
        return "Transition-heavy counter attacks"
    if year == 2021:
        return "Structural instability"
    return "High-press + build-up mismatch"


def merge_manutd_data() -> pd.DataFrame:
    pca_df = pd.read_csv(PCA_SCORES_PATH)
    pca_mu = pca_df[pca_df["Squad"] == TEAM_NAME].copy()
    if pca_mu.empty:
        raise SystemExit(f"No PCA data found for {TEAM_NAME}")

    pca_mu["season_year"] = pca_mu["Season"].apply(season_start_year)
    pca_mu["Season_hyphen"] = pca_mu["Season"].apply(season_to_hyphen)

    league_df = pd.read_csv(LEAGUE_STATS_PATH)
    league_mu = league_df[league_df["Squad"] == TEAM_NAME].copy()
    league_mu["season_year"] = league_mu["season"].apply(season_start_year)
    league_mu = league_mu[["season", "season_year", "Pts", "Pts/MP"]].copy()
    league_mu = league_mu.rename(columns={"season": "Season_hyphen", "Pts/MP": "points_per_match"})

    merged = pca_mu.merge(league_mu, on=["Season_hyphen", "season_year"], how="left")
    merged["manager_phase"] = merged["season_year"].apply(manager_for_year)
    merged["tactical_era"] = merged["season_year"].apply(tactical_era_for_year)

    merged = merged.sort_values("season_year").reset_index(drop=True)
    merged["league_rank"] = merged["Pts"].rank(ascending=False, method="min")
    merged["season_label"] = merged["Season"].str.replace("_", "-")
    merged["competitiveness_rank"] = merged["season_rank_by_index"]

    if merged[["Pts", "points_per_match"]].isna().any().any():
        raise SystemExit("Missing league performance fields after merge. Check season naming consistency.")

    return merged


def add_manager_bands(ax: plt.Axes, df: pd.DataFrame) -> None:
    # Intentionally left blank: event/phase annotations removed for clean plotting.
    _ = (ax, df)


def plot_index_vs_results(df: pd.DataFrame, output_path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(12, 6))

    x = df["season_year"]
    ax1.plot(x, df["competitiveness_index"], marker="o", linewidth=2.2, color=STYLE_COLORS[0])
    ax1.set_xlabel("Season")
    ax1.set_ylabel("Competitiveness Index", color=STYLE_COLORS[0])
    ax1.tick_params(axis="y", labelcolor=STYLE_COLORS[0])

    ax1.yaxis.set_major_locator(LinearLocator(7))
    ax1.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))

    add_manager_bands(ax1, df)

    ax1.set_xticks(df["season_year"])
    ax1.set_xticklabels(df["season_label"], rotation=35, ha="right")
    ax1.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_pc_components(df: pd.DataFrame, output_path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(df))
    width = 0.24
    ax.bar(x - width, df["PC1"], width=width, color=STYLE_COLORS[0], label="PC1")
    ax.bar(x, df["PC2"], width=width, color=STYLE_COLORS[1], label="PC2")
    ax.bar(x + width, df["PC3"], width=width, color=STYLE_COLORS[2], label="PC3")

    ax.axhline(0, color="black", linewidth=1)
    ax.legend(loc="best", frameon=True)
    ax.set_xticks(x)
    ax.set_xticklabels(df["season_label"], rotation=35, ha="right")
    ax.set_xlabel("Season")
    ax.set_ylabel("PC Score")
    ax.yaxis.set_major_locator(MaxNLocator(nbins=7))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_pc1_pc2_trajectory(df: pd.DataFrame, output_path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 8))

    for i in range(len(df) - 1):
        ax.annotate(
            "",
            xy=(df.loc[i + 1, "PC1"], df.loc[i + 1, "PC2"]),
            xytext=(df.loc[i, "PC1"], df.loc[i, "PC2"]),
            arrowprops={"arrowstyle": "->", "lw": 1.6, "alpha": 0.6, "color": "#7f8c8d"},
        )

    for _, row in df.iterrows():
        ax.scatter(row["PC1"], row["PC2"], s=120, color=STYLE_COLORS[0], edgecolor="black", linewidth=0.5)

    ax.axhline(0, linestyle="--", color="gray", linewidth=1)
    ax.axvline(0, linestyle="--", color="gray", linewidth=1)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.xaxis.set_major_locator(MaxNLocator(nbins=7))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=7))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_rank_comparison(df: pd.DataFrame, output_path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))

    x = df["season_year"]
    ax.plot(x, df["league_rank"], marker="o", linewidth=2.2, color=STYLE_COLORS[3])
    ax.plot(
        x,
        df["competitiveness_rank"],
        marker="s",
        linewidth=2.2,
        color=STYLE_COLORS[0],
    )

    ax.set_xticks(df["season_year"])
    ax.set_xticklabels(df["season_label"], rotation=35, ha="right")
    ax.set_xlabel("Season")
    ax.set_ylabel("Rank")
    ax.invert_yaxis()
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    merged = merge_manutd_data()

    merged.to_csv(OUTPUT_DIR / "manutd_competitiveness_story_dataset.csv", index=False)

    plot_index_vs_results(merged, OUTPUT_DIR / "manutd_index_vs_results.png")
    plot_pc_components(merged, OUTPUT_DIR / "manutd_pc_components.png")
    plot_pc1_pc2_trajectory(merged, OUTPUT_DIR / "manutd_pc1_pc2_trajectory.png")
    plot_rank_comparison(merged, OUTPUT_DIR / "manutd_rank_comparison.png")

    print("Generated charts:")
    print("- manutd_index_vs_results.png")
    print("- manutd_pc_components.png")
    print("- manutd_pc1_pc2_trajectory.png")
    print("- manutd_rank_comparison.png")
    print("- manutd_competitiveness_story_dataset.csv")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()