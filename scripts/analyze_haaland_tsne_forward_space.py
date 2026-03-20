#!/usr/bin/env python3
"""
t-SNE Manifold Visualization: Haaland's extreme position among EPL forwards.
Visualizes all EPL forwards in 2D space to show Haaland's unique ecological niche.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE

DATA_ROOT = Path("data")
OUTPUT_DIR = Path("chapter4_player_role")

# Player metrics for visualization
PLAYER_METRICS = [
    "goals_90",
    "shots_total_90",
    "shots_on_target_90",
    "assists_90",
    "fouls_committed",
    "red_cards",
]

METRIC_FILES = {
    "goals_90": "goals_90.csv",
    "shots_total_90": "shots_total_90.csv",
    "shots_on_target_90": "shots_on_target_90.csv",
    "assists_90": "assists_90.csv",
    "fouls_committed": "fouls_committed.csv",
    "red_cards": "red_cards.csv",
}

HAALAND_NAME = "Erling Haaland"


def parse_player_team(text: str) -> tuple[str, str]:
    """Parse 'Player Name • Team Name' format."""
    text = str(text).replace("\u00a0", " ").strip()
    if " • " in text:
        parts = text.split(" • ")
        return parts[0].strip(), parts[1].strip()
    return text, ""


def extract_forward_metrics(data_root: Path, seasons: list[str]) -> pd.DataFrame:
    """Extract all forward player metrics across seasons."""
    all_rows = []

    for season in seasons:
        folder = data_root / f"fbref_pl_{season}"
        if not folder.exists():
            continue

        season_year = int(season.split("_")[0])
        season_data = {}

        # Load all metrics for this season
        for metric, filename in METRIC_FILES.items():
            file_path = folder / filename
            if not file_path.exists():
                continue

            try:
                # Read without header (these files have indices in first column)
                df = pd.read_csv(file_path, header=None)
                if df.shape[1] < 3:
                    continue

                # Extract player-team names and values
                player_col = df.iloc[:, 1]
                value_col = df.iloc[:, 2]
                
                metric_map = {}
                for p_name, value in zip(player_col, value_col):
                    p_name = str(p_name).strip()
                    try:
                        value = float(value)
                        player, team = parse_player_team(p_name)
                        key = (player, team)
                        metric_map[key] = value
                    except (ValueError, TypeError):
                        continue

                season_data[metric] = metric_map
            except Exception as e:
                print(f"Warning: Could not process {filename}: {e}")

        # Build rows for this season
        all_keys = set()
        for metric_dict in season_data.values():
            all_keys.update(metric_dict.keys())

        for player, team in all_keys:
            row_dict = {
                "player": player,
                "team": team,
                "season": season,
                "season_year": season_year,
            }
            for metric in PLAYER_METRICS:
                if metric in season_data:
                    row_dict[metric] = season_data[metric].get((player, team), np.nan)
                else:
                    row_dict[metric] = np.nan

            all_rows.append(row_dict)

    df_all = pd.DataFrame(all_rows)

    # Filter to recent seasons and drop nulls
    df_all = df_all[df_all["season_year"] >= 2022]
    df_all = df_all.dropna(subset=PLAYER_METRICS)

    # Rough forward filter (players with at least some goals or shots)
    df_all = df_all[
        (df_all["goals_90"] > 0.1) | (df_all["shots_total_90"] > 1.0)
    ].reset_index(drop=True)

    return df_all


def apply_tsne(df: pd.DataFrame) -> np.ndarray:
    """Apply t-SNE dimensionality reduction."""
    X = df[PLAYER_METRICS].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(df) - 1), n_iter=1000)
    X_2d = tsne.fit_transform(X_scaled)

    return X_2d


def plot_tsne_forwards(df: pd.DataFrame, X_2d: np.ndarray, output_path: Path) -> None:
    """Plot t-SNE visualization with Haaland highlighted."""
    fig, ax = plt.subplots(figsize=(12, 10))

    # Regular forwards
    is_haaland = df["player"] == HAALAND_NAME
    regular = ~is_haaland

    ax.scatter(
        X_2d[regular, 0],
        X_2d[regular, 1],
        c="#3949ab",
        s=100,
        alpha=0.6,
        edgecolors="black",
        linewidth=0.5,
        label="Other Forwards",
    )

    # Haaland (very prominent)
    if is_haaland.any():
        haaland_idx = np.where(is_haaland)[0]
        ax.scatter(
            X_2d[haaland_idx, 0],
            X_2d[haaland_idx, 1],
            c="#ff006e",
            s=500,
            alpha=0.95,
            edgecolors="darkred",
            linewidth=2,
            marker="*",
            label="Erling Haaland",
            zorder=10,
        )
        # Annotate Haaland
        for idx in haaland_idx:
            ax.annotate(
                "Haaland",
                (X_2d[idx, 0], X_2d[idx, 1]),
                fontsize=11,
                fontweight="bold",
                xytext=(10, 10),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.7),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
            )

    # Annotate a few other notable players
    top_scorers = df.nlargest(3, "goals_90")
    for _, row in top_scorers.iterrows():
        if row["player"] != HAALAND_NAME:
            idx = df.index.get_loc(_)
            if idx < len(X_2d):
                ax.annotate(
                    row["player"].split()[0],  # Use first name only
                    (X_2d[idx, 0], X_2d[idx, 1]),
                    fontsize=8,
                    alpha=0.7,
                    xytext=(5, 5),
                    textcoords="offset points",
                )

    ax.set_xlabel("t-SNE Dimension 1", fontweight="bold")
    ax.set_ylabel("t-SNE Dimension 2", fontweight="bold")
    ax.set_title(
        "EPL Forwards in t-SNE Space (2022-2024)\nHaaland's Extreme Position in Offensive Action Space",
        fontweight="bold",
        fontsize=13,
    )
    ax.legend(fontsize=10, loc="best")
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def export_player_metrics(df: pd.DataFrame, output_path: Path) -> None:
    """Export processed player metrics for reference."""
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

    # Print Haaland's stats
    haaland_data = df[df["player"] == HAALAND_NAME]
    if not haaland_data.empty:
        print(f"\nHaaland's offensive metrics summary:")
        print(haaland_data[["player", "team", "season", *PLAYER_METRICS]].to_string())


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    seasons = [
        "2022_2023",
        "2023_2024",
        "2024_2025",
    ]

    print(f"Extracting forward metrics for seasons: {seasons}")
    df = extract_forward_metrics(DATA_ROOT, seasons)

    print(f"Extracted {len(df)} forward-season records")
    if len(df) < 10:
        print("WARNING: Too few records. Expanding season range...")
        seasons = [
            "2021_2022",
            "2022_2023",
            "2023_2024",
            "2024_2025",
        ]
        df = extract_forward_metrics(DATA_ROOT, seasons)
        print(f"Expanded to {len(df)} forward-season records")

    if len(df) < 5:
        print("ERROR: Insufficient data for visualization.")
        return

    print(f"Applying t-SNE to {len(df)} records...")
    X_2d = apply_tsne(df)

    plot_tsne_forwards(df, X_2d, OUTPUT_DIR / "haaland_tsne_forward_space.png")

    export_player_metrics(df, OUTPUT_DIR / "epl_forward_metrics_2022_2024.csv")

    print("\nt-SNE analysis complete.")


if __name__ == "__main__":
    main()
