#!/usr/bin/env python3
"""Style evolution analysis for 12-variable factor and clustering outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

TOP_6_TEAMS = [
    "Manchester City",
    "Liverpool",
    "Chelsea",
    "Arsenal",
    "Manchester Utd",
    "Tottenham Hotspur",
]

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.unicode_minus"] = False


def parse_season_year(series: pd.Series) -> pd.Series:
    season = series.astype(str).str.replace("_", "-", regex=False)
    return season.str.split("-").str[0].astype(int)


def plot_top6_factors(df_scores: pd.DataFrame, factor_cols: list[str], output_path: Path) -> None:
    n_factors = len(factor_cols)
    fig, axes = plt.subplots(1, n_factors, figsize=(6 * n_factors, 5))
    if n_factors == 1:
        axes = [axes]

    palette = sns.color_palette("Set2", n_colors=len(TOP_6_TEAMS))
    for i, factor in enumerate(factor_cols):
        ax = axes[i]
        for j, team in enumerate(TOP_6_TEAMS):
            sub = df_scores[df_scores["Squad"] == team].sort_values("season_year")
            if sub.empty:
                continue
            ax.plot(sub["season_year"], sub[factor], marker="o", linewidth=2, label=team, color=palette[j])
        ax.axhline(0, linestyle="--", linewidth=1, color="gray", alpha=0.7)
        ax.set_title(f"Top-6 Evolution: {factor}", fontweight="bold")
        ax.set_xlabel("Season")
        ax.set_ylabel("Factor Score")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_league_factor_trends(df_scores: pd.DataFrame, factor_cols: list[str], output_path: Path) -> pd.DataFrame:
    grouped = df_scores.groupby("season_year")[factor_cols].agg(["mean", "std"])
    years = grouped.index.to_numpy()

    n_factors = len(factor_cols)
    fig, axes = plt.subplots(1, n_factors, figsize=(6 * n_factors, 5))
    if n_factors == 1:
        axes = [axes]

    trend_rows = []
    for i, factor in enumerate(factor_cols):
        ax = axes[i]
        mean_vals = grouped[(factor, "mean")].to_numpy()
        std_vals = grouped[(factor, "std")].to_numpy()

        ax.plot(years, mean_vals, marker="o", linewidth=2.2, color="#1f77b4")
        ax.fill_between(years, mean_vals - std_vals, mean_vals + std_vals, alpha=0.2, color="#1f77b4")

        slope, intercept = np.polyfit(years, mean_vals, 1)
        ax.plot(years, slope * years + intercept, "r--", linewidth=1.5, alpha=0.8)

        trend_rows.append(
            {
                "factor": factor,
                "slope_per_year": slope,
                "mean_2016": float(mean_vals[0]),
                "mean_2024": float(mean_vals[-1]),
                "change_2016_to_2024": float(mean_vals[-1] - mean_vals[0]),
            }
        )

        ax.axhline(0, linestyle="--", linewidth=1, color="gray", alpha=0.7)
        ax.set_title(f"League Trend: {factor}", fontweight="bold")
        ax.set_xlabel("Season")
        ax.set_ylabel("Mean Score")
        ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return pd.DataFrame(trend_rows)


def plot_cluster_shares(df_cluster: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    counts = (
        df_cluster.groupby(["season_year", "Cluster"]).size().unstack(fill_value=0).sort_index(axis=1)
    )
    shares = counts.div(counts.sum(axis=1), axis=0)

    fig, ax = plt.subplots(figsize=(10, 6))
    shares.plot(kind="area", stacked=True, alpha=0.85, ax=ax, colormap="tab10")
    ax.set_title("Cluster Share Evolution by Season", fontweight="bold")
    ax.set_xlabel("Season")
    ax.set_ylabel("Share of Teams")
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.2)
    ax.legend(title="Cluster", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return shares.reset_index()


def build_summary_markdown(
    trend_df: pd.DataFrame,
    cluster_share_df: pd.DataFrame,
    output_path: Path,
) -> None:
    strongest_up = trend_df.sort_values("slope_per_year", ascending=False).iloc[0]
    strongest_down = trend_df.sort_values("slope_per_year", ascending=True).iloc[0]

    first_year = int(cluster_share_df["season_year"].min())
    last_year = int(cluster_share_df["season_year"].max())

    cluster_cols = [c for c in cluster_share_df.columns if c != "season_year"]
    first_row = cluster_share_df[cluster_share_df["season_year"] == first_year].iloc[0]
    last_row = cluster_share_df[cluster_share_df["season_year"] == last_year].iloc[0]

    cluster_changes = []
    for c in cluster_cols:
        cluster_changes.append((c, float(last_row[c] - first_row[c])))
    cluster_changes.sort(key=lambda x: x[1], reverse=True)

    lines = [
        "# 12变量版本风格演变分析摘要",
        "",
        "## 1. 联赛因子趋势",
        f"- 上升最快因子: `{strongest_up['factor']}` (年斜率 {strongest_up['slope_per_year']:.4f})",
        f"- 下降最快因子: `{strongest_down['factor']}` (年斜率 {strongest_down['slope_per_year']:.4f})",
        "",
        "## 2. 聚类结构演变",
        f"- 赛季范围: {first_year}-{last_year}",
        f"- 占比上升最多: `Cluster {cluster_changes[0][0]}` ({cluster_changes[0][1]:+.2%})",
        f"- 占比下降最多: `Cluster {cluster_changes[-1][0]}` ({cluster_changes[-1][1]:+.2%})",
        "",
        "## 3. 输出文件",
        "- `style_evolution_top6_12vars.png`",
        "- `style_evolution_league_trends_12vars.png`",
        "- `style_evolution_cluster_shares_12vars.png`",
        "- `style_evolution_trends_12vars.csv`",
        "- `style_evolution_cluster_shares_12vars.csv`",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run style evolution analysis for 12-variable results.")
    parser.add_argument(
        "--factor-scores",
        default="data/derived/team_factor_scores_12vars_2016_2025.csv",
        help="Factor score CSV path.",
    )
    parser.add_argument(
        "--clusters",
        default="data/derived/team_clusters_assigned_12vars.csv",
        help="Cluster assignment CSV path.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/derived",
        help="Output directory.",
    )
    args = parser.parse_args()

    scores_path = Path(args.factor_scores)
    cluster_path = Path(args.clusters)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not scores_path.exists():
        raise SystemExit(f"Factor scores not found: {scores_path}")
    if not cluster_path.exists():
        raise SystemExit(f"Cluster assignments not found: {cluster_path}")

    df_scores = pd.read_csv(scores_path)
    df_cluster = pd.read_csv(cluster_path)

    factor_cols = [c for c in df_scores.columns if c.startswith("Factor")]
    if not factor_cols:
        raise SystemExit("No factor columns detected in factor score file.")

    df_scores["season_year"] = parse_season_year(df_scores["Season"])
    df_cluster["season_year"] = parse_season_year(df_cluster["Season"])

    top6_plot = output_dir / "style_evolution_top6_12vars.png"
    league_plot = output_dir / "style_evolution_league_trends_12vars.png"
    cluster_plot = output_dir / "style_evolution_cluster_shares_12vars.png"
    trend_csv = output_dir / "style_evolution_trends_12vars.csv"
    cluster_csv = output_dir / "style_evolution_cluster_shares_12vars.csv"
    summary_md = output_dir / "style_evolution_summary_12vars.md"

    plot_top6_factors(df_scores, factor_cols, top6_plot)
    trend_df = plot_league_factor_trends(df_scores, factor_cols, league_plot)
    cluster_share_df = plot_cluster_shares(df_cluster, cluster_plot)

    trend_df.to_csv(trend_csv, index=False)
    cluster_share_df.to_csv(cluster_csv, index=False)
    build_summary_markdown(trend_df, cluster_share_df, summary_md)

    print(f"Saved: {top6_plot}")
    print(f"Saved: {league_plot}")
    print(f"Saved: {cluster_plot}")
    print(f"Saved: {trend_csv}")
    print(f"Saved: {cluster_csv}")
    print(f"Saved: {summary_md}")


if __name__ == "__main__":
    main()
