#!/usr/bin/env python3
"""
Temporal Feature Importance Tracking: Season-by-season analysis of Man City's tactical weights.
Creates pseudo-samples by ranking 20 EPL teams to build valid RF datasets for each season.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

DATA_ROOT = Path("data")
OUTPUT_DIR = Path("chapter4_player_role")
STYLE_CSV = "style_metrics_all.csv"

RF_FEATURES = [
    "shots_per_match",
    "shots_on_target_per_match",
    "goals_per_match",
    "cross_volume_per_match",
    "fouls_per_match",
    "interceptions_per_match",
    "tackles_won_per_match",
    "goals_against_per_match",
]

FEATURE_LABELS = {
    "shots_per_match": "Shots",
    "shots_on_target_per_match": "Shots on Target",
    "goals_per_match": "Goals",
    "cross_volume_per_match": "Crosses",
    "fouls_per_match": "Fouls",
    "interceptions_per_match": "Interceptions",
    "tackles_won_per_match": "Tackles Won",
    "goals_against_per_match": "Goals Against",
}


def load_full_league_data(style_csv: Path) -> pd.DataFrame:
    """Load all teams' data for all seasons."""
    df = pd.read_csv(style_csv)
    df["season_year"] = df["Season"].astype(str).str.replace("-", "_").str.split("_").str[0].astype(int)
    df = df[(df["season_year"] >= 2016) & (df["season_year"] <= 2024)].sort_values(["season_year", "Squad"])
    return df


def train_season_models(league_data: pd.DataFrame) -> pd.DataFrame:
    """Train RF models for each season using all teams' data."""
    results = []
    
    for season_year in sorted(league_data["season_year"].unique()):
        season_data = league_data[league_data["season_year"] == season_year].copy()
        
        if len(season_data) < 5:
            print(f"Skipping {season_year}: only {len(season_data)} teams")
            continue
        
        # Prepare features and target
        X = season_data[RF_FEATURES].fillna(0)
        
        # Target: teams sorted by points (we use an approximation based on goals/defense balance)
        # In a real scenario, we'd have actual points; here we use a composite metric
        season_data["proxy_points"] = (
            season_data["goals_per_match"] * 3 - 
            season_data["goals_against_per_match"] * 1.5
        )
        y = (season_data["proxy_points"] >= season_data["proxy_points"].median()).astype(int)
        
        # Skip if no variance
        if y.nunique() < 2:
            continue
        
        # Train model
        if len(X) >= 5:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            model = RandomForestClassifier(
                n_estimators=20, max_depth=3, random_state=42, n_jobs=-1
            )
            model.fit(X_scaled, y)
            
            # Store results
            for feat, imp in zip(RF_FEATURES, model.feature_importances_):
                results.append({
                    "Season": f"{season_year}_{season_year+1}",
                    "season_year": season_year,
                    "Feature": feat,
                    "Importance": imp,
                    "n_samples": len(X),
                })
            
            print(f"✓ {season_year}-{season_year+1} (n={len(X)} teams): trained")
    
    return pd.DataFrame(results)


def plot_temporal_evolution(results_df: pd.DataFrame, output_path: Path) -> None:
    """Plot feature importance evolution over time."""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(RF_FEATURES)))
    
    for feat, color in zip(RF_FEATURES, colors):
        subset = results_df[results_df["Feature"] == feat].sort_values("season_year")
        if len(subset) > 0:
            ax.plot(
                subset["season_year"],
                subset["Importance"],
                marker="o",
                linewidth=2.5,
                markersize=8,
                label=FEATURE_LABELS[feat],
                color=color,
            )
    
    # Mark Haaland joining
    ax.axvline(2022, color="red", linestyle="--", linewidth=2.5, alpha=0.8, label="Haaland Joins (2022-23)")
    ax.axvspan(2022, 2024.5, alpha=0.08, color="red")
    ax.text(2023, 0.35, "Post-Haaland Era", fontsize=12, color="darkred", fontweight="bold", ha="center")
    
    ax.set_xlabel("Season Start Year", fontweight="bold", fontsize=12)
    ax.set_ylabel("Feature Importance Score", fontweight="bold", fontsize=12)
    ax.set_title(
        "Man City: Temporal Evolution of Winning Factors (2016-2025)\n"
        "Season-by-Season Feature Importance Tracking",
        fontweight="bold",
        fontsize=13,
    )
    ax.grid(alpha=0.3, linestyle="--")
    ax.legend(fontsize=9, loc="upper left", ncol=2, framealpha=0.95)
    ax.set_xlim(2015.5, 2024.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_feature_trajectory_heatmap(results_df: pd.DataFrame, output_path: Path) -> None:
    """Plot feature importance as heatmap."""
    pivot = results_df.pivot_table(
        index="Feature", columns="season_year", values="Importance"
    )
    
    if pivot.empty:
        print("No data for heatmap")
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=0, vmax=0.35)
    
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([FEATURE_LABELS.get(f, f) for f in pivot.index])
    
    # Mark Haaland joining
    for i, year in enumerate(pivot.columns):
        if year >= 2022:
            ax.axvline(i - 0.5, color="red", linewidth=2.5, linestyle="--")
            break
    
    ax.set_xlabel("Season Start Year", fontweight="bold")
    ax.set_ylabel("Feature", fontweight="bold")
    ax.set_title(
        "Feature Importance Heatmap: Pre vs Post-Haaland Visual Contrast",
        fontweight="bold",
    )
    
    cbar = plt.colorbar(im, ax=ax, label="Importance")
    
    # Annotations
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            if pd.notna(val):
                ax.text(
                    j, i, f"{val:.2f}",
                    ha="center", va="center",
                    color="white" if val > 0.15 else "black",
                    fontsize=8, fontweight="bold"
                )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def compute_feature_changes(results_df: pd.DataFrame) -> pd.DataFrame:
    """Compute pre vs post changes for each feature."""
    pre = results_df[results_df["season_year"] <= 2021].groupby("Feature")["Importance"].mean()
    post = results_df[results_df["season_year"] >= 2022].groupby("Feature")["Importance"].mean()
    
    changes = pd.DataFrame({
        "Feature": RF_FEATURES,
    })
    changes["Pre_Mean"] = changes["Feature"].map(lambda f: pre.get(f, np.nan))
    changes["Post_Mean"] = changes["Feature"].map(lambda f: post.get(f, np.nan))
    changes["Change"] = changes["Post_Mean"] - changes["Pre_Mean"]
    changes["Change_%"] = (changes["Change"] / (changes["Pre_Mean"] + 1e-6)) * 100
    changes["Feature_Label"] = changes["Feature"].map(FEATURE_LABELS)
    
    return changes.sort_values("Change_%", ascending=False)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Loading full league data...")
    league_data = load_full_league_data(STYLE_CSV)
    print(f"Total records: {len(league_data)} (teams × seasons)")
    
    print("\nTraining season-by-season models...\n")
    results_df = train_season_models(league_data)
    
    if results_df.empty:
        print("ERROR: No valid models trained.")
        return
    
    n_seasons = results_df["season_year"].nunique()
    print(f"\n✓ Successfully trained models for {n_seasons} seasons")
    
    # Save results
    results_csv = OUTPUT_DIR / "haaland_temporal_feature_importance.csv"
    results_df.to_csv(results_csv, index=False)
    print(f"Saved: {results_csv}")
    
    # Compute and save changes
    changes = compute_feature_changes(results_df)
    changes_csv = OUTPUT_DIR / "haaland_temporal_feature_changes.csv"
    changes.to_csv(changes_csv, index=False)
    print(f"Saved: {changes_csv}")
    
    print("\n" + "="*70)
    print("PRE-HAALAND (2016-2021) vs POST-HAALAND (2022-2024)")
    print("="*70)
    print(changes[["Feature_Label", "Pre_Mean", "Post_Mean", "Change_%"]].to_string(index=False))
    print("="*70)
    
    # Visualizations
    plot_temporal_evolution(results_df, OUTPUT_DIR / "haaland_temporal_feature_evolution.png")
    plot_feature_trajectory_heatmap(results_df, OUTPUT_DIR / "haaland_feature_importance_heatmap.png")


if __name__ == "__main__":
    main()
