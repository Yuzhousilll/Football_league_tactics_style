#!/usr/bin/env python3
"""
Dual Mode Feature Importance Analysis:
- Classification Mode: Binary target (high/low points)
- Regression Mode: Continuous target (actual points)
Compares both approaches for robustness.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
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
RF_FEATURES = [
    "shots_per_match",
    "shots_on_target_per_match",
    "goals_per_match",
    "cross_volume_per_match",
    "interceptions_per_match",
    "tackles_won_per_match",
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
FEATURE_LABELS = {
    "shots_per_match": "Shots",
    "shots_on_target_per_match": "Shots on Target",
    "goals_per_match": "Goals",
    "cross_volume_per_match": "Crosses",
    "interceptions_per_match": "Interceptions",
    "tackles_won_per_match": "Tackles Won",
}


def load_full_league_data(style_csv: Path) -> pd.DataFrame:
    """Load all teams' data for all seasons."""
    df = pd.read_csv(style_csv)
    df["season_year"] = df["Season"].astype(str).str.replace("-", "_").str.split("_").str[0].astype(int)
    df = df[(df["season_year"] >= 2016) & (df["season_year"] <= 2024)].sort_values(["season_year", "Squad"])
    return df


def train_season_models(league_data: pd.DataFrame, mode: str = "regression") -> pd.DataFrame:
    """
    Train RF models for each season.
    
    mode='regression': Use actual points as continuous target
    mode='classification': Use binary (high/low points) target
    """
    results = []
    
    for season_year in sorted(league_data["season_year"].unique()):
        season_data = league_data[league_data["season_year"] == season_year].copy()
        
        if len(season_data) < 5:
            print(f"Skipping {season_year}: only {len(season_data)} teams")
            continue
        
        # Prepare features
        X = season_data[RF_FEATURES].fillna(0)
        
        if mode == "regression":
            # Use actual points (if available) or proxy
            if "points" in season_data.columns:
                y = season_data["points"].values
            else:
                # Fallback: use proxy based on goals/defense
                y = (season_data["goals_per_match"] * 3 - season_data["goals_against_per_match"] * 1.5).values
        else:  # classification
            # Binary target: high vs low points
            season_data["proxy_points"] = (
                season_data["goals_per_match"] * 3 - 
                season_data["goals_against_per_match"] * 1.5
            )
            y = (season_data["proxy_points"] >= season_data["proxy_points"].median()).astype(int).values
            
            # Skip if no variance
            if len(np.unique(y)) < 2:
                print(f"Skipping {season_year}: no target variance in classification mode")
                continue
        
        # Train model
        if len(X) >= 5:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            if mode == "regression":
                model = RandomForestRegressor(n_estimators=20, max_depth=4, random_state=42, n_jobs=-1)
            else:
                model = RandomForestClassifier(n_estimators=20, max_depth=3, random_state=42, n_jobs=-1)
            
            model.fit(X_scaled, y)
            
            # Store results
            for feat, imp in zip(RF_FEATURES, model.feature_importances_):
                results.append({
                    "Season": f"{season_year}_{season_year+1}",
                    "season_year": season_year,
                    "Feature": feat,
                    "Importance": imp,
                    "n_samples": len(X),
                    "mode": mode,
                })
            
            mode_label = "REGR" if mode == "regression" else "CLSF"
            print(f"✓ {season_year}-{season_year+1} ({mode_label}, n={len(X)}): trained")
    
    return pd.DataFrame(results)


def plot_comparison(clf_results: pd.DataFrame, reg_results: pd.DataFrame, output_path: Path) -> None:
    """Plot side-by-side comparison of classification vs regression feature importance."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(RF_FEATURES)))
    
    for mode, results, ax, title_suffix in [
        ("classification", clf_results, axes[0], "Binary Classification\n(High/Low Points)"),
        ("regression", reg_results, axes[1], "Continuous Regression\n(Actual Points)"),
    ]:
        for feat, color in zip(RF_FEATURES, colors):
            subset = results[results["Feature"] == feat].sort_values("season_year")
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
        ax.axvline(2022, color="red", linestyle="--", linewidth=2.5, alpha=0.8)
        ax.axvspan(2022, 2024.5, alpha=0.08, color="red")
        ax.text(2023, ax.get_ylim()[1] * 0.85, "Post-Haaland", 
               fontsize=11, color="darkred", fontweight="bold", ha="center")
        
        ax.set_xlabel("Season Start Year", fontweight="bold", fontsize=11)
        ax.set_ylabel("Feature Importance", fontweight="bold", fontsize=11)
        ax.set_title(f"Man City Winning Factors Evolution\n{title_suffix}", 
                    fontweight="bold", fontsize=12)
        ax.grid(alpha=0.3, linestyle="--")
        ax.set_xlim(2015.5, 2024.5)
    
    axes[0].legend(fontsize=8.5, loc="upper left", ncol=2, framealpha=0.95)
    
    fig.suptitle("Feature Importance: Classification vs Regression Comparison", 
                fontweight="bold", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def compute_changes_table(clf_results: pd.DataFrame, reg_results: pd.DataFrame) -> pd.DataFrame:
    """Compare pre vs post changes between classification and regression modes."""
    changes = []
    
    for mode_name, results in [("Classification", clf_results), ("Regression", reg_results)]:
        pre = results[results["season_year"] <= 2021].groupby("Feature")["Importance"].mean()
        post = results[results["season_year"] >= 2022].groupby("Feature")["Importance"].mean()
        
        for feat in RF_FEATURES:
            pre_val = pre.get(feat, np.nan)
            post_val = post.get(feat, np.nan)
            
            if pd.notna(pre_val) and pd.notna(post_val):
                change_pct = (post_val - pre_val) / (pre_val + 1e-6) * 100
                changes.append({
                    "Feature": feat,
                    "Feature_Label": FEATURE_LABELS[feat],
                    "Mode": mode_name,
                    "Pre": pre_val,
                    "Post": post_val,
                    "Change_%": change_pct,
                })
    
    return pd.DataFrame(changes)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Loading full league data...")
    league_data = load_full_league_data(STYLE_CSV)
    print(f"Total records: {len(league_data)} (teams × seasons)\n")
    
    print("="*70)
    print("CLASSIFICATION MODE: Binary target (High/Low Points)")
    print("="*70)
    clf_results = train_season_models(league_data, mode="classification")
    print()
    
    print("="*70)
    print("REGRESSION MODE: Continuous target (Actual Points)")
    print("="*70)
    reg_results = train_season_models(league_data, mode="regression")
    print()
    
    if clf_results.empty or reg_results.empty:
        print("ERROR: Failed to train models.")
        return
    
    # Save raw results
    clf_csv = OUTPUT_DIR / "haaland_temporal_classification_importance.csv"
    reg_csv = OUTPUT_DIR / "haaland_temporal_regression_importance.csv"
    clf_results.to_csv(clf_csv, index=False)
    reg_results.to_csv(reg_csv, index=False)
    print(f"Saved: {clf_csv}")
    print(f"Saved: {reg_csv}\n")
    
    # Compute and save comparison
    changes = compute_changes_table(clf_results, reg_results)
    changes_csv = OUTPUT_DIR / "haaland_temporal_mode_comparison.csv"
    changes.to_csv(changes_csv, index=False)
    print(f"Saved: {changes_csv}\n")
    
    # Display results
    print("="*80)
    print("PRE-HAALAND (2016-2021) vs POST-HAALAND (2022-2024): MODE COMPARISON")
    print("="*80)
    print(changes.to_string(index=False))
    print("="*80)
    
    # Visualization
    plot_comparison(clf_results, reg_results, OUTPUT_DIR / "haaland_classification_vs_regression.png")


if __name__ == "__main__":
    main()
