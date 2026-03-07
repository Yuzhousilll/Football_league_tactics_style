#!/usr/bin/env python3
"""Team clustering analysis based on factor scores."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False

DEFAULT_INPUT = "data/derived/team_factor_scores_2016_2025.csv"
DEFAULT_OUTPUT_DIR = "data/derived"
DEFAULT_N_CLUSTERS = 4


def compute_cluster_statistics(df: pd.DataFrame, factor_cols: list[str]) -> pd.DataFrame:
    """Compute mean factor values for each cluster."""
    stats = df.groupby('Cluster')[factor_cols].mean()
    stats['Count'] = df.groupby('Cluster').size()
    return stats


def plot_cluster_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: Path,
    title: str = "Team Clustering",
):
    """Create scatter plot of clusters in 2D factor space."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    clusters = sorted(df['Cluster'].unique())
    colors = sns.color_palette('tab10', len(clusters))
    
    for cluster_id, color in zip(clusters, colors):
        cluster_data = df[df['Cluster'] == cluster_id]
        ax.scatter(
            cluster_data[x_col],
            cluster_data[y_col],
            c=[color],
            label=f'Cluster {cluster_id}',
            alpha=0.6,
            s=50,
            edgecolors='black',
            linewidths=0.5,
        )
    
    ax.set_xlabel(x_col, fontsize=12)
    ax.set_ylabel(y_col, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(title='Cluster', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_cluster_heatmap(stats: pd.DataFrame, output_path: Path):
    """Create heatmap showing cluster centers."""
    factor_cols = [col for col in stats.columns if col.startswith('Factor')]
    data = stats[factor_cols]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(
        data.T,
        annot=True,
        fmt='.2f',
        cmap='RdBu_r',
        center=0,
        cbar_kws={'label': 'Factor Score'},
        linewidths=0.5,
        ax=ax,
    )
    
    ax.set_xlabel('Cluster', fontsize=12)
    ax.set_ylabel('Factor', fontsize=12)
    ax.set_title('Cluster Centers (Mean Factor Scores)', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_cluster_distribution(df: pd.DataFrame, output_path: Path):
    """Create bar chart showing cluster size distribution."""
    cluster_counts = df['Cluster'].value_counts().sort_index()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(
        cluster_counts.index,
        cluster_counts.values,
        color=sns.color_palette('tab10', len(cluster_counts)),
        edgecolor='black',
        linewidth=1.5,
    )
    
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f'{int(height)}',
            ha='center',
            va='bottom',
            fontsize=11,
            fontweight='bold',
        )
    
    ax.set_xlabel('Cluster', fontsize=12)
    ax.set_ylabel('Number of Teams', fontsize=12)
    ax.set_title('Team Distribution Across Clusters', fontsize=14, fontweight='bold')
    ax.set_xticks(cluster_counts.index)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_season_cluster_evolution(df: pd.DataFrame, output_path: Path, top_n: int = 6):
    """Show evolution of top teams across clusters over seasons."""
    team_counts = df['Squad'].value_counts().head(top_n)
    top_teams = team_counts.index.tolist()
    
    seasons = sorted(df['Season'].unique())
    
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()
    
    for idx, team in enumerate(top_teams):
        ax = axes[idx]
        team_data = df[df['Squad'] == team].sort_values('Season')
        
        ax.plot(
            range(len(team_data)),
            team_data['Cluster'],
            marker='o',
            linewidth=2,
            markersize=8,
            label=team,
        )
        
        ax.set_xticks(range(len(team_data)))
        ax.set_xticklabels(team_data['Season'], rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Cluster', fontsize=10)
        ax.set_title(team, fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_yticks(sorted(df['Cluster'].unique()))
    
    plt.suptitle('Top Teams: Cluster Evolution Over Seasons', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster teams based on factor scores.")
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help=f"Input factor scores CSV (default: {DEFAULT_INPUT}).",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=DEFAULT_N_CLUSTERS,
        help=f"Number of clusters (default: {DEFAULT_N_CLUSTERS}).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    factor_cols = [col for col in df.columns if col.startswith('Factor')]
    
    if not factor_cols:
        raise SystemExit("No factor columns found in input data.")

    X = df[factor_cols].to_numpy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=args.n_clusters, random_state=42, n_init=20)
    df['Cluster'] = kmeans.fit_predict(X_scaled)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cluster_stats = compute_cluster_statistics(df, factor_cols)
    
    stats_path = output_dir / "team_cluster_statistics.csv"
    cluster_stats.to_csv(stats_path)

    clusters_path = output_dir / "team_clusters_assigned.csv"
    df.to_csv(clusters_path, index=False)

    plot_cluster_scatter(
        df,
        'Factor1',
        'Factor2',
        output_dir / "cluster_scatter_f1_f2.png",
        "Team Clustering: Factor1 vs Factor2",
    )

    if len(factor_cols) >= 3:
        plot_cluster_scatter(
            df,
            'Factor1',
            'Factor3',
            output_dir / "cluster_scatter_f1_f3.png",
            "Team Clustering: Factor1 vs Factor3",
        )

    plot_cluster_heatmap(cluster_stats, output_dir / "cluster_centers_heatmap.png")
    plot_cluster_distribution(df, output_dir / "cluster_distribution.png")
    plot_season_cluster_evolution(df, output_dir / "top_teams_cluster_evolution.png")

    summary_lines = [
        "Team Clustering Analysis Summary",
        f"Input: {input_path}",
        f"Number of clusters: {args.n_clusters}",
        f"Total teams analyzed: {len(df)}",
        f"Factor columns: {', '.join(factor_cols)}",
        "",
        "Cluster Statistics:",
        cluster_stats.to_string(),
        "",
        f"Output files:",
        f"  - Cluster assignments: {clusters_path}",
        f"  - Cluster statistics: {stats_path}",
        f"  - Scatter plots: cluster_scatter_*.png",
        f"  - Heatmap: cluster_centers_heatmap.png",
        f"  - Distribution: cluster_distribution.png",
        f"  - Evolution: top_teams_cluster_evolution.png",
    ]
    
    summary_path = output_dir / "team_clustering_summary.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"Clustering completed. {args.n_clusters} clusters identified.")
    print(f"Results saved to: {output_dir}")
    print(f"\nCluster sizes:")
    print(df['Cluster'].value_counts().sort_index())


if __name__ == "__main__":
    main()
