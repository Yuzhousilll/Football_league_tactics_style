#!/usr/bin/env python3
"""Select factor-analysis variables from all dimensions in style_metrics_all.csv."""

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
MISSING_THRESHOLD = 0.2
COMMUNALITY_THRESHOLD = 0.35
LOADING_THRESHOLD = 0.4
MAX_FACTORS = 6

EXCLUDE_COLS = {"Season", "Squad"}


def season_start_year(season_label: str) -> int:
    normalized = season_label.replace("_", "-")
    match = re.match(r"^(\d{4})-\d{4}$", normalized)
    if not match:
        raise ValueError(f"Invalid season label: {season_label}")
    return int(match.group(1))


def season_in_range(season_label: str, start: str, end: str) -> bool:
    year = season_start_year(season_label)
    return season_start_year(start) <= year <= season_start_year(end)


def choose_factor_count(x_scaled: np.ndarray, max_factors: int) -> int:
    corr = np.corrcoef(x_scaled, rowvar=False)
    eigenvalues = np.linalg.eigvalsh(corr)
    suggested = int((eigenvalues > 1.0).sum())
    return max(1, min(max_factors, suggested, x_scaled.shape[1] - 1))


def compute_kmo(x_scaled: np.ndarray) -> float:
    corr = np.corrcoef(x_scaled, rowvar=False)
    inv_corr = np.linalg.pinv(corr)
    partial = -inv_corr / np.sqrt(np.outer(np.diag(inv_corr), np.diag(inv_corr)))
    np.fill_diagonal(partial, 0)

    corr_sq_sum = (corr**2).sum() - np.sum(np.diag(corr**2))
    partial_sq_sum = (partial**2).sum() - np.sum(np.diag(partial**2))
    return float(corr_sq_sum / (corr_sq_sum + partial_sq_sum))


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen all dimensions and select FA variables.")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--season-start", default=DEFAULT_SEASON_START)
    parser.add_argument("--season-end", default=DEFAULT_SEASON_END)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    if "Season" not in df.columns:
        raise SystemExit("Input must contain 'Season' column.")

    filtered = df[df["Season"].apply(lambda s: season_in_range(str(s), args.season_start, args.season_end))].copy()
    if filtered.empty:
        raise SystemExit("No rows left after season filter.")

    # 1) Collect all numeric dimensions from original table.
    numeric_cols = []
    for col in filtered.columns:
        if col in EXCLUDE_COLS:
            continue
        if pd.api.types.is_numeric_dtype(filtered[col]):
            numeric_cols.append(col)

    if len(numeric_cols) < 4:
        raise SystemExit("Not enough numeric dimensions for factor analysis.")

    missing_rate = filtered[numeric_cols].isna().mean()
    candidate_cols = [c for c in numeric_cols if missing_rate[c] <= MISSING_THRESHOLD]

    # 2) Median impute to keep as many dimensions as possible.
    work = filtered[candidate_cols].copy()
    work = work.fillna(work.median(numeric_only=True))

    # Remove constant columns if any.
    variances = work.var(axis=0)
    candidate_cols = [c for c in candidate_cols if variances[c] > 1e-10]
    work = work[candidate_cols]

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(work.to_numpy(dtype=float))

    n_factors = choose_factor_count(x_scaled, MAX_FACTORS)
    model = FactorAnalysis(n_components=n_factors, random_state=42)
    scores = model.fit_transform(x_scaled)

    loading_cols = [f"Factor{i}" for i in range(1, n_factors + 1)]
    loadings_df = pd.DataFrame(model.components_.T, index=candidate_cols, columns=loading_cols)

    screening = pd.DataFrame(index=candidate_cols)
    screening["missing_rate"] = missing_rate[candidate_cols]
    screening["communality"] = (loadings_df**2).sum(axis=1)
    screening["max_abs_loading"] = loadings_df.abs().max(axis=1)
    screening["recommended"] = (
        (screening["communality"] >= COMMUNALITY_THRESHOLD)
        & (screening["max_abs_loading"] >= LOADING_THRESHOLD)
    )

    recommended_vars = screening[screening["recommended"]].index.tolist()

    if len(recommended_vars) < 5:
        # Fallback: keep top variables by communality if strict threshold is too harsh.
        recommended_vars = (
            screening.sort_values(["communality", "max_abs_loading"], ascending=False)
            .head(min(8, len(screening)))
            .index.tolist()
        )

    final_work = filtered[recommended_vars].copy().fillna(filtered[recommended_vars].median(numeric_only=True))
    final_scaled = scaler.fit_transform(final_work.to_numpy(dtype=float))
    final_factors = choose_factor_count(final_scaled, MAX_FACTORS)
    final_model = FactorAnalysis(n_components=final_factors, random_state=42)
    final_scores = final_model.fit_transform(final_scaled)

    final_loading_cols = [f"Factor{i}" for i in range(1, final_factors + 1)]
    final_loadings = pd.DataFrame(final_model.components_.T, index=recommended_vars, columns=final_loading_cols)
    final_loadings["communality"] = (final_loadings[final_loading_cols] ** 2).sum(axis=1)

    score_df = filtered[["Season", "Squad"]].reset_index(drop=True)
    for i, col in enumerate(final_loading_cols):
        score_df[col] = final_scores[:, i]

    kmo_value = compute_kmo(final_scaled)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    screen_path = out_dir / "full_dimensions_variable_screening.csv"
    loadings_path = out_dir / "full_dimensions_factor_loadings.csv"
    scores_path = out_dir / "full_dimensions_factor_scores.csv"
    summary_path = out_dir / "full_dimensions_fa_summary.txt"

    screening.reset_index(names="variable").sort_values("communality", ascending=False).to_csv(screen_path, index=False)
    final_loadings.reset_index(names="variable").to_csv(loadings_path, index=False)
    score_df.to_csv(scores_path, index=False)

    lines = [
        "Full-Dimensions Factor Analysis Summary",
        f"Input: {input_path}",
        f"Season range: {args.season_start} to {args.season_end}",
        f"Rows used: {len(filtered)}",
        f"Original numeric dimensions: {len(numeric_cols)}",
        f"Candidate dimensions after missing/variance filter: {len(candidate_cols)}",
        f"Recommended dimensions: {len(recommended_vars)}",
        f"Recommended variables: {', '.join(recommended_vars)}",
        f"Final factor count (eigenvalue > 1): {final_factors}",
        f"KMO (recommended set): {kmo_value:.4f}",
        f"Screening output: {screen_path}",
        f"Loadings output: {loadings_path}",
        f"Scores output: {scores_path}",
    ]
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Saved: {screen_path}")
    print(f"Saved: {loadings_path}")
    print(f"Saved: {scores_path}")
    print(f"Saved: {summary_path}")
    print("Recommended variables:")
    for var in recommended_vars:
        print(f"- {var}")


if __name__ == "__main__":
    main()
