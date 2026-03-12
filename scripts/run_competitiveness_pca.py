#!/usr/bin/env python3
"""Run PCA for Chapter 3 competitiveness evaluation using on-pitch action variables."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import chi2
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

INPUT_CSV = "style_metrics_all.csv"
OUTPUT_DIR = "chapter3_competitiveness"
TOP_TEAMS = [
    "Manchester City",
    "Liverpool",
    "Chelsea",
    "Arsenal",
    "Manchester Utd",
    "Tottenham Hotspur",
]

PCA_VARIABLES = [
    "shots_per_match",
    "shots_on_target_per_match",
    "assists_per_match",
    "cross_volume_per_match",
    "penalties_won_per_match",
    "tackles_won_per_match",
    "interceptions_per_match",
    "fouls_drawn_per_match",
]

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.unicode_minus"] = False


def season_start_year(season: str) -> int:
    return int(str(season).replace("-", "_").split("_")[0])


def compute_kmo(x_scaled: np.ndarray) -> float:
    corr = np.corrcoef(x_scaled, rowvar=False)
    inv_corr = np.linalg.pinv(corr)
    partial = -inv_corr / np.sqrt(np.outer(np.diag(inv_corr), np.diag(inv_corr)))
    np.fill_diagonal(partial, 0)

    corr_sq_sum = (corr**2).sum() - np.sum(np.diag(corr**2))
    partial_sq_sum = (partial**2).sum() - np.sum(np.diag(partial**2))
    return float(corr_sq_sum / (corr_sq_sum + partial_sq_sum))


def bartlett_sphericity_test(x_scaled: np.ndarray) -> tuple[float, float, int]:
    n_samples, n_vars = x_scaled.shape
    corr = np.corrcoef(x_scaled, rowvar=False)
    det_corr = max(np.linalg.det(corr), 1e-12)
    chi_square = -(n_samples - 1 - (2 * n_vars + 5) / 6) * np.log(det_corr)
    dof = n_vars * (n_vars - 1) // 2
    p_value = float(1 - chi2.cdf(chi_square, dof))
    return float(chi_square), p_value, dof


def load_action_data(input_path: Path, season_start: int, season_end: int) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    required_cols = ["Season", "Squad", *PCA_VARIABLES]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise SystemExit(f"Missing required columns: {missing_cols}")

    df = df[df["Season"].apply(lambda s: season_start <= season_start_year(s) <= season_end)].copy()
    df = df[required_cols].copy()
    df[PCA_VARIABLES] = df[PCA_VARIABLES].fillna(df[PCA_VARIABLES].median(numeric_only=True))
    df["season_year"] = df["Season"].apply(season_start_year)
    return df.sort_values(["season_year", "Squad"]).reset_index(drop=True)


def choose_component_count(pca: PCA) -> int:
    eigenvalues = pca.explained_variance_
    count = int((eigenvalues > 1.0).sum())
    return max(1, count)


def plot_scree(explained_variance: np.ndarray, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    pcs = np.arange(1, len(explained_variance) + 1)
    ax.plot(pcs, explained_variance, marker="o", linewidth=2)
    ax.axhline(1.0, linestyle="--", color="red", linewidth=1.5)
    ax.set_xlabel("Principal Component")
    ax.set_ylabel("Eigenvalue")
    ax.set_title("Scree Plot for Action-Based PCA", fontweight="bold")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_loadings_heatmap(loadings_df: pd.DataFrame, pc_cols: list[str], output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(
        loadings_df[pc_cols],
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        linewidths=0.5,
        ax=ax,
        cbar_kws={"label": "Loading"},
    )
    ax.set_title("Action-Based PCA Loadings Heatmap", fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_pc_scatter(scores_df: pd.DataFrame, output_path: Path) -> None:
    if "PC2" not in scores_df.columns:
        return

    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(
        scores_df["PC1"],
        scores_df["PC2"],
        c=scores_df["assists_per_match"],
        cmap="viridis",
        alpha=0.75,
        s=45,
        edgecolors="black",
        linewidths=0.3,
    )
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Assists per Match")
    ax.axhline(0, linestyle="--", color="gray", linewidth=1)
    ax.axvline(0, linestyle="--", color="gray", linewidth=1)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title("Team-Season Action Profile in PC Space", fontweight="bold")
    ax.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_top_team_evolution(scores_df: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    palette = sns.color_palette("Set2", n_colors=len(TOP_TEAMS))
    for idx, team in enumerate(TOP_TEAMS):
        team_df = scores_df[scores_df["Squad"] == team].sort_values("season_year")
        if team_df.empty:
            continue
        ax.plot(
            team_df["season_year"],
            team_df["competitiveness_index"],
            marker="o",
            linewidth=2,
            label=team,
            color=palette[idx],
        )
    ax.set_xlabel("Season")
    ax.set_ylabel("Action-Based Competitiveness Index")
    ax.set_title("Top-Team Action-Based Competitiveness Evolution", fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_season_distribution(scores_df: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.boxplot(data=scores_df, x="Season", y="competitiveness_index", ax=ax, color="#7db7d9")
    ax.set_xlabel("Season")
    ax.set_ylabel("Action-Based Competitiveness Index")
    ax.set_title("Seasonal Distribution of Action-Based Competitiveness", fontweight="bold")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PCA for Chapter 3 using on-pitch action variables.")
    parser.add_argument("--input", default=INPUT_CSV)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--season-start", type=int, default=2016)
    parser.add_argument("--season-end", type=int, default=2024)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    data = load_action_data(input_path, args.season_start, args.season_end)

    x = data[PCA_VARIABLES].astype(float).to_numpy()
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    pca_full = PCA()
    pca_full.fit(x_scaled)
    n_components = choose_component_count(pca_full)

    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(x_scaled)
    pc_cols = [f"PC{i}" for i in range(1, n_components + 1)]

    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
    loadings_df = pd.DataFrame(loadings, index=PCA_VARIABLES, columns=pc_cols)
    loadings_df["communality"] = (loadings_df[pc_cols] ** 2).sum(axis=1)

    scores_df = data.copy()
    for i, col in enumerate(pc_cols):
        scores_df[col] = scores[:, i]

    if "PC2" not in scores_df.columns and pca_full.n_components_ >= 2:
        visual_scores = pca_full.transform(x_scaled)[:, :2]
        scores_df["PC1"] = visual_scores[:, 0]
        scores_df["PC2"] = visual_scores[:, 1]

    weights = pca.explained_variance_ratio_ / pca.explained_variance_ratio_.sum()
    scores_df["competitiveness_index"] = scores[:, :n_components] @ weights
    scores_df["season_rank_by_index"] = (
        scores_df.groupby("Season")["competitiveness_index"].rank(ascending=False, method="min")
    )

    kmo = compute_kmo(x_scaled)
    bartlett_chi2, bartlett_p, bartlett_dof = bartlett_sphericity_test(x_scaled)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = output_dir / "competitiveness_dataset.csv"
    loadings_path = output_dir / "competitiveness_pca_loadings.csv"
    scores_path = output_dir / "competitiveness_pca_scores.csv"
    summary_path = output_dir / "competitiveness_pca_summary.txt"
    scree_path = output_dir / "competitiveness_scree_plot.png"
    heatmap_path = output_dir / "competitiveness_loadings_heatmap.png"
    scatter_path = output_dir / "competitiveness_pc1_pc2_scatter.png"
    top6_path = output_dir / "competitiveness_top6_evolution.png"
    season_box_path = output_dir / "competitiveness_season_distribution.png"

    data.to_csv(dataset_path, index=False)
    loadings_df.reset_index(names="variable").to_csv(loadings_path, index=False)
    scores_df.to_csv(scores_path, index=False)

    plot_scree(pca_full.explained_variance_, scree_path)
    plot_loadings_heatmap(loadings_df, pc_cols, heatmap_path)
    plot_pc_scatter(scores_df, scatter_path)
    plot_top_team_evolution(scores_df, top6_path)
    plot_season_distribution(scores_df, season_box_path)

    lines = [
        "Action-Based Competitiveness PCA Summary",
        f"Observations: {len(data)}",
        f"Seasons: {args.season_start}-{args.season_end}",
        f"Variables: {', '.join(PCA_VARIABLES)}",
        f"Selected components: {n_components}",
        f"Explained variance ratio: {', '.join(f'{v:.4f}' for v in pca.explained_variance_ratio_)}",
        f"Cumulative explained variance: {pca.explained_variance_ratio_.sum():.4f}",
        f"KMO: {kmo:.4f}",
        f"Bartlett chi2: {bartlett_chi2:.4f}",
        f"Bartlett dof: {bartlett_dof}",
        f"Bartlett p-value: {bartlett_p:.8f}",
        f"Dataset output: {dataset_path}",
        f"Loadings output: {loadings_path}",
        f"Scores output: {scores_path}",
    ]
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Saved: {dataset_path}")
    print(f"Saved: {loadings_path}")
    print(f"Saved: {scores_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {scree_path}")
    print(f"Saved: {heatmap_path}")
    print(f"Saved: {scatter_path}")
    print(f"Saved: {top6_path}")
    print(f"Saved: {season_box_path}")
    print(f"Selected components: {n_components}")
    print(f"Cumulative explained variance: {pca.explained_variance_ratio_.sum():.4f}")
    print(f"KMO: {kmo:.4f}")
    print(f"Bartlett p-value: {bartlett_p:.8f}")


if __name__ == "__main__":
    main()
