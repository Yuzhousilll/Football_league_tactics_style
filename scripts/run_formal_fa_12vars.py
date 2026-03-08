#!/usr/bin/env python3
"""Run formal factor analysis with the selected 12 variables."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler

DEFAULT_INPUT = "style_metrics_all.csv"
DEFAULT_OUTPUT_DIR = "data/derived"
DEFAULT_SEASON_START = "2016-2017"
DEFAULT_SEASON_END = "2024-2025"
DEFAULT_MAX_FACTORS = 6

FACTOR_VARIABLES_12 = [
    "shots_on_target_per_match",
    "goals_per_match",
    "goals_per_sot",
    "cross_share_of_touches",
    "penalties_won_per_match",
    "offsides_to_shots_ratio",
    "goals_against_per_match",
    "clean_sheet_pct",
    "tackles_won_per_match",
    "interceptions_per_match",
    "shots_on_target_against_per_match",
    "players_used",
]


plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.unicode_minus"] = False


def season_start_year(season_label: str) -> int:
    normalized = season_label.replace("_", "-")
    match = re.match(r"^(\d{4})-\d{4}$", normalized)
    if not match:
        raise ValueError(f"Invalid season label: {season_label}")
    return int(match.group(1))


def season_in_range(season_label: str, start: str, end: str) -> bool:
    year = season_start_year(season_label)
    return season_start_year(start) <= year <= season_start_year(end)


def choose_factor_count_from_corr(corr: np.ndarray, max_factors: int) -> int:
    eigenvalues = np.linalg.eigvalsh(corr)
    suggested = int((eigenvalues > 1.0).sum())
    return max(1, min(max_factors, suggested, corr.shape[0] - 1))


def plot_scree(eigenvalues_desc: np.ndarray, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(eigenvalues_desc) + 1), eigenvalues_desc, marker="o", linewidth=2)
    ax.axhline(y=1.0, color="red", linestyle="--", linewidth=1.5, label="Eigenvalue = 1")
    ax.set_xlabel("Component")
    ax.set_ylabel("Eigenvalue")
    ax.set_title("Scree Plot (12 Variables)", fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_loadings_heatmap(loadings: pd.DataFrame, factor_cols: list[str], output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(
        loadings[factor_cols],
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        linewidths=0.5,
        cbar_kws={"label": "Loading"},
        ax=ax,
    )
    ax.set_title("Factor Loadings Heatmap (12 Variables)", fontweight="bold")
    ax.set_xlabel("Factor")
    ax.set_ylabel("Variable")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Formal FA with selected 12 variables.")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--season-start", default=DEFAULT_SEASON_START)
    parser.add_argument("--season-end", default=DEFAULT_SEASON_END)
    parser.add_argument("--max-factors", type=int, default=DEFAULT_MAX_FACTORS)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    required = ["Season", "Squad", *FACTOR_VARIABLES_12]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    filtered = df[df["Season"].apply(lambda s: season_in_range(str(s), args.season_start, args.season_end))].copy()
    if filtered.empty:
        raise SystemExit("No rows left after season filter.")

    work = filtered[FACTOR_VARIABLES_12].copy()
    work = work.fillna(work.median(numeric_only=True))

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(work.to_numpy(dtype=float))

    corr = np.corrcoef(x_scaled, rowvar=False)
    eigenvalues = np.linalg.eigvalsh(corr)
    eigenvalues_desc = np.sort(eigenvalues)[::-1]
    n_factors = choose_factor_count_from_corr(corr, args.max_factors)

    model = FactorAnalysis(n_components=n_factors, random_state=42)
    factor_scores = model.fit_transform(x_scaled)

    factor_cols = [f"Factor{i}" for i in range(1, n_factors + 1)]
    loadings = pd.DataFrame(model.components_.T, index=FACTOR_VARIABLES_12, columns=factor_cols)
    loadings["communality"] = (loadings[factor_cols] ** 2).sum(axis=1)

    scores = filtered[["Season", "Squad"]].reset_index(drop=True)
    for i, col in enumerate(factor_cols):
        scores[col] = factor_scores[:, i]

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    season_tag = f"{season_start_year(args.season_start)}_{season_start_year(args.season_end) + 1}"
    tag = "12vars"

    loadings_path = out_dir / f"team_factor_loadings_{tag}_{season_tag}.csv"
    scores_path = out_dir / f"team_factor_scores_{tag}_{season_tag}.csv"
    summary_path = out_dir / f"team_factor_summary_{tag}_{season_tag}.txt"
    scree_path = out_dir / f"scree_plot_{tag}.png"
    heatmap_path = out_dir / f"factor_loadings_heatmap_{tag}.png"

    loadings.reset_index(names="variable").to_csv(loadings_path, index=False)
    scores.to_csv(scores_path, index=False)
    plot_scree(eigenvalues_desc, scree_path)
    plot_loadings_heatmap(loadings, factor_cols, heatmap_path)

    total_explained = float((eigenvalues_desc[:n_factors].sum() / len(FACTOR_VARIABLES_12)) * 100)

    summary_lines = [
        "Formal Team Factor Analysis Summary (12 Variables)",
        f"Input: {input_path}",
        f"Season range: {args.season_start} to {args.season_end}",
        f"Rows used: {len(filtered)}",
        f"Variables: {', '.join(FACTOR_VARIABLES_12)}",
        f"Factors extracted: {n_factors}",
        f"Approx explained variance (%): {total_explained:.2f}",
        f"Loadings output: {loadings_path}",
        f"Scores output: {scores_path}",
        f"Scree plot: {scree_path}",
        f"Loadings heatmap: {heatmap_path}",
    ]
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"Saved: {loadings_path}")
    print(f"Saved: {scores_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {scree_path}")
    print(f"Saved: {heatmap_path}")
    print(f"Factors extracted: {n_factors}")
    print(f"Approx explained variance (%): {total_explained:.2f}")


if __name__ == "__main__":
    main()
