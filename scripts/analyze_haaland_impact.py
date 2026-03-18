#!/usr/bin/env python3
"""Analyze star-player impact (Haaland) and Manchester City offensive tactical shift."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

DATA_ROOT = Path("data")
OUTPUT_DIR = Path("chapter4_player_role")
PLAYER_NAME = "Erling Haaland"
TEAM_NAME = "Manchester City"

PLAYER_METRICS = {
    "goals_total": ("goals.csv", "Goals"),
    "goals_per90": ("goals_90.csv", "Goals per 90"),
    "shots_per90": ("shots_total_90.csv", "Shots per 90"),
}

CITY_METRICS = [
    "shots_per_match",
    "shots_on_target_per_match",
    "goals_per_match",
    "assists_per_match",
    "cross_volume_per_match",
    "penalties_won_per_match",
]

TREND_METRICS = [
    "shots_per_match",
    "shots_on_target_per_match",
    "goals_per_match",
    "cross_volume_per_match",
]

TREND_METRIC_COLORS = {
    "shots_per_match": "#1f77b4",
    "shots_on_target_per_match": "#ff7f0e",
    "goals_per_match": "#006400",
    "cross_volume_per_match": "#d62728",
}

CITY_METRIC_LABELS = {
    "shots_per_match": "Shots/Match",
    "shots_on_target_per_match": "Shots on Target/Match",
    "goals_per_match": "Goals/Match",
    "assists_per_match": "Assists/Match",
    "cross_volume_per_match": "Crosses/Match",
    "penalties_won_per_match": "Penalties Won/Match",
}

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.unicode_minus"] = False


def season_start_year(season_label: str) -> int:
    return int(str(season_label).replace("-", "_").split("_")[0])


def parse_player_name(player_team_text: str) -> str:
    text = str(player_team_text).replace("\u00a0", " ").strip()
    return text.split(" • ")[0].strip()


def extract_haaland_vs_peers(data_root: Path, season_start: int = 2022, season_end: int = 2024) -> pd.DataFrame:
    rows: list[dict] = []
    folders = sorted(data_root.glob("fbref_pl_*"))

    for folder in folders:
        season = folder.name.replace("fbref_pl_", "")
        year = season_start_year(season)
        if not (season_start <= year <= season_end):
            continue

        for metric_key, (file_name, _) in PLAYER_METRICS.items():
            file_path = folder / file_name
            if not file_path.exists():
                continue

            df = pd.read_csv(file_path)
            if df.shape[1] < 3:
                continue

            player_col = df.columns[1]
            value_col = df.columns[2]
            work = df[[player_col, value_col]].copy()
            work.columns = ["player_team", "value"]
            work["player"] = work["player_team"].apply(parse_player_name)
            work["value"] = pd.to_numeric(work["value"], errors="coerce")
            work = work.dropna(subset=["value"])

            if work.empty:
                continue

            haaland_vals = work.loc[work["player"] == PLAYER_NAME, "value"]
            haaland_value = float(haaland_vals.iloc[0]) if not haaland_vals.empty else np.nan

            peers = work.loc[work["player"] != PLAYER_NAME, "value"]
            peers_avg = float(peers.mean()) if not peers.empty else np.nan
            peers_std = float(peers.std(ddof=0)) if len(peers) > 1 else np.nan

            rows.append(
                {
                    "Season": season,
                    "season_year": year,
                    "metric": metric_key,
                    "haaland_value": haaland_value,
                    "peers_avg": peers_avg,
                    "peers_std": peers_std,
                    "n_peers": int(peers.shape[0]),
                }
            )

    return pd.DataFrame(rows).sort_values(["season_year", "metric"]).reset_index(drop=True)


def plot_haaland_vs_peers(df: pd.DataFrame, output_path: Path) -> None:
    season_order = ["2022_2023", "2023_2024", "2024_2025"]
    season_labels = ["22-23", "23-24", "24-25"]
    season_to_x = {season: idx for idx, season in enumerate(season_order)}

    metric_order = list(PLAYER_METRICS.keys())
    n = len(metric_order)
    fig, axes = plt.subplots(1, n, figsize=(5.8 * n, 5), sharex=True)
    if n == 1:
        axes = [axes]

    for i, metric in enumerate(metric_order):
        ax = axes[i]
        sub = df[df["metric"] == metric].copy()
        sub = sub[sub["Season"].isin(season_order)]
        sub["x"] = sub["Season"].map(season_to_x)
        sub = sub.sort_values("x")
        if sub.empty:
            ax.set_visible(False)
            continue

        label = PLAYER_METRICS[metric][1]
        ax.plot(sub["x"], sub["haaland_value"], marker="o", linewidth=2.5, color="#0b6e4f", label="Haaland")
        ax.plot(sub["x"], sub["peers_avg"], marker="o", linewidth=2.0, color="#c44536", linestyle="--", label="Other Players Avg")

        if sub["peers_std"].notna().any():
            lower = sub["peers_avg"] - sub["peers_std"].fillna(0)
            upper = sub["peers_avg"] + sub["peers_std"].fillna(0)
            ax.fill_between(sub["x"], lower, upper, alpha=0.18, color="#c44536")

        ax.set_title(label, fontweight="bold")
        ax.set_xlabel("Season")
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(season_labels)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)

    axes[0].set_ylabel("Value")
    fig.suptitle("Haaland Offensive Output vs Other Players (Since Joining EPL)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def load_mancity_style_metrics(style_csv: Path, season_start: int = 2016, season_end: int = 2024) -> pd.DataFrame:
    df = pd.read_csv(style_csv)
    needed = ["Season", "Squad", *CITY_METRICS]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns in style_metrics_all.csv: {missing}")

    city = df[df["Squad"] == TEAM_NAME].copy()
    city["season_year"] = city["Season"].apply(season_start_year)
    city = city[(city["season_year"] >= season_start) & (city["season_year"] <= season_end)].copy()
    return city.sort_values("season_year").reset_index(drop=True)


def compute_pre_post(city_df: pd.DataFrame, split_year: int = 2022) -> pd.DataFrame:
    pre = city_df[city_df["season_year"] <= split_year - 1]
    post = city_df[city_df["season_year"] >= split_year]

    rows = []
    for metric in CITY_METRICS:
        pre_mean = float(pre[metric].mean())
        post_mean = float(post[metric].mean())
        pct_change = ((post_mean - pre_mean) / pre_mean * 100.0) if pre_mean != 0 else np.nan
        rows.append(
            {
                "metric": metric,
                "metric_label": CITY_METRIC_LABELS[metric],
                "pre_2016_2021_mean": pre_mean,
                "post_2022_2024_mean": post_mean,
                "pct_change": pct_change,
            }
        )

    return pd.DataFrame(rows)


def plot_pre_post_bars(comp_df: pd.DataFrame, output_path: Path) -> None:
    plot_df = comp_df.copy()
    x = np.arange(len(plot_df))
    w = 0.38

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - w / 2, plot_df["pre_2016_2021_mean"], width=w, label="Pre-Haaland (2016-2021)", color="#3a86ff")
    ax.bar(x + w / 2, plot_df["post_2022_2024_mean"], width=w, label="Post-Haaland (2022-2024)", color="#ff006e")

    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["metric_label"], rotation=20, ha="right")
    ax.set_ylabel("Mean Value")
    ax.set_title("Manchester City Offensive Actions: Pre vs Post 2022-23", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()

    for i, row in plot_df.reset_index(drop=True).iterrows():
        ax.text(i, max(row["pre_2016_2021_mean"], row["post_2022_2024_mean"]) * 1.02, f"{row['pct_change']:+.1f}%", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_tactical_shift_trend(city_df: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))

    for metric in TREND_METRICS:
        values = city_df[metric].to_numpy(dtype=float)
        z = (values - values.mean()) / (values.std(ddof=0) if values.std(ddof=0) != 0 else 1)
        ax.plot(
            city_df["season_year"],
            z,
            marker="o",
            linewidth=2,
            label=CITY_METRIC_LABELS[metric],
            color=TREND_METRIC_COLORS.get(metric),
        )

    ax.axvline(2022, color="black", linestyle="--", linewidth=1.5, label="Haaland joined (2022-23)")
    ax.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("Season")
    ax.set_ylabel("Standardized value (z-score)")
    ax.set_title("Manchester City Tactical Shift in Offensive Actions", fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Chapter 4 charts for Haaland impact analysis.")
    parser.add_argument("--data-root", default=str(DATA_ROOT))
    parser.add_argument("--style-metrics", default="style_metrics_all.csv")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    haaland_df = extract_haaland_vs_peers(Path(args.data_root), season_start=2022, season_end=2024)
    haaland_csv = output_dir / "haaland_vs_peers_offense.csv"
    haaland_fig = output_dir / "haaland_vs_peers_offense.png"
    haaland_df.to_csv(haaland_csv, index=False)
    plot_haaland_vs_peers(haaland_df, haaland_fig)

    city_df = load_mancity_style_metrics(Path(args.style_metrics), season_start=2016, season_end=2024)
    comp_df = compute_pre_post(city_df, split_year=2022)
    comp_csv = output_dir / "mancity_offense_pre_post_comparison.csv"
    prepost_fig = output_dir / "mancity_pre_post_haaland_offense.png"
    trend_fig = output_dir / "mancity_offense_tactical_shift_trend.png"

    comp_df.to_csv(comp_csv, index=False)
    plot_pre_post_bars(comp_df, prepost_fig)
    plot_tactical_shift_trend(city_df, trend_fig)

    print(f"Saved: {haaland_csv}")
    print(f"Saved: {haaland_fig}")
    print(f"Saved: {comp_csv}")
    print(f"Saved: {prepost_fig}")
    print(f"Saved: {trend_fig}")
if __name__ == "__main__":
    main()
