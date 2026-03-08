#!/usr/bin/env python3
"""Team-level factor analysis for selected PL style metrics."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler

DEFAULT_INPUT = "style_metrics_all.csv"
DEFAULT_OUTPUT_DIR = "data/derived"
DEFAULT_SEASON_START = "2016-2017"
DEFAULT_SEASON_END = "2024-2025"

FACTOR_VARIABLES = [
    "shots_on_target_per_match",
    "goals_per_sot",
    "cross_share_of_touches",
    "tackles_won_per_match",
    "interceptions_per_match",
    "shots_on_target_against_per_match",
]


def season_start_year(season_label: str) -> int:
    normalized = season_label.replace("_", "-")
    match = re.match(r"^(\d{4})-\d{4}$", normalized)
    if not match:
        raise ValueError(f"Invalid season label: {season_label}")
    return int(match.group(1))


def season_in_range(season_label: str, start: str, end: str) -> bool:
    year = season_start_year(season_label)
    start_year = season_start_year(start)
    end_year = season_start_year(end)
    return start_year <= year <= end_year


def choose_factor_count(x_scaled: np.ndarray, max_factors: int) -> int:
    corr = np.corrcoef(x_scaled, rowvar=False)
    eigenvalues = np.linalg.eigvalsh(corr)
    suggested = int((eigenvalues > 1.0).sum())
    return max(1, min(max_factors, suggested))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run team-level factor analysis on style metrics.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"Input CSV path (default: {DEFAULT_INPUT}).")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--season-start",
        default=DEFAULT_SEASON_START,
        help=f"Start season (default: {DEFAULT_SEASON_START}).",
    )
    parser.add_argument(
        "--season-end",
        default=DEFAULT_SEASON_END,
        help=f"End season (default: {DEFAULT_SEASON_END}).",
    )
    parser.add_argument(
        "--max-factors",
        type=int,
        default=5,
        help="Maximum number of factors to extract (default: 5).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    required_cols = ["Season", "Squad", *FACTOR_VARIABLES]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise SystemExit(f"Missing required columns: {missing_cols}")

    filtered = df[df["Season"].apply(lambda s: season_in_range(str(s), args.season_start, args.season_end))].copy()
    filtered = filtered.dropna(subset=FACTOR_VARIABLES)

    if filtered.empty:
        raise SystemExit("No rows left after season filtering and NA removal.")

    x = filtered[FACTOR_VARIABLES].astype(float).to_numpy()
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    n_factors = choose_factor_count(x_scaled, args.max_factors)
    model = FactorAnalysis(n_components=n_factors, random_state=42)
    factor_scores = model.fit_transform(x_scaled)

    loading_cols = [f"Factor{i}" for i in range(1, n_factors + 1)]
    loadings = pd.DataFrame(model.components_.T, index=FACTOR_VARIABLES, columns=loading_cols).reset_index()
    loadings = loadings.rename(columns={"index": "variable"})
    loadings["communality"] = (loadings[loading_cols] ** 2).sum(axis=1)

    scores = filtered[["Season", "Squad"]].reset_index(drop=True)
    for i, col in enumerate(loading_cols):
        scores[col] = factor_scores[:, i]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    season_tag = f"{season_start_year(args.season_start)}_{season_start_year(args.season_end)+1}"
    vars_tag = "6vars"  # 标记使用6个变量的版本
    loadings_path = output_dir / f"team_factor_loadings_{vars_tag}_{season_tag}.csv"
    scores_path = output_dir / f"team_factor_scores_{vars_tag}_{season_tag}.csv"
    summary_path = output_dir / f"team_factor_summary_{vars_tag}_{season_tag}.txt"

    loadings.to_csv(loadings_path, index=False)
    scores.to_csv(scores_path, index=False)

    summary_lines = [
        "Team Factor Analysis Summary",
        f"Input: {input_path}",
        f"Season range: {args.season_start} to {args.season_end}",
        f"Rows used: {len(filtered)}",
        f"Variables: {', '.join(FACTOR_VARIABLES)}",
        f"Factors extracted: {n_factors}",
        f"Loadings output: {loadings_path}",
        f"Scores output: {scores_path}",
    ]
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"Saved: {loadings_path}")
    print(f"Saved: {scores_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
