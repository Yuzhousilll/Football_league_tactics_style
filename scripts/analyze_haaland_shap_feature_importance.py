#!/usr/bin/env python3
"""
Random Forest Analysis: Did Haaland change Man City's winning formula?
Feature importance comparison before and after Haaland's joining.
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


def load_mancity_with_results(style_csv: Path) -> pd.DataFrame:
    """Load Man City style metrics from 2016-2024."""
    df = pd.read_csv(style_csv)
    city = df[df["Squad"] == "Manchester City"].copy()
    city["season_year"] = city["Season"].astype(str).str.replace("-", "_").str.split("_").str[0].astype(int)
    city = city[(city["season_year"] >= 2016) & (city["season_year"] <= 2024)].sort_values("season_year")
    return city


def load_team_results_points() -> pd.DataFrame:
    """Extract points per season from results files."""
    rows = []
    for folder in sorted(DATA_ROOT.glob("fbref_pl_*")):
        season = folder.name.replace("fbref_pl_", "")
        year = int(season.split("_")[0])
        if not (2016 <= year <= 2024):
            continue

        results_file = folder / "results2022_202391_overall.csv"
        if not results_file.exists():
            pattern = list(folder.glob("results*_overall.csv"))
            if pattern:
                results_file = pattern[0]
            else:
                continue

        try:
            res_df = pd.read_csv(results_file)
            city_row = res_df[res_df["Squad"] == "Manchester City"]
            if not city_row.empty:
                pts = float(city_row.iloc[0]["Pts"])
                rows.append({"Season": season, "season_year": year, "points": pts})
        except Exception as e:
            print(f"Warning: Could not parse {results_file}: {e}")

    return pd.DataFrame(rows)


def prepare_rf_data(style_df: pd.DataFrame, results_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Merge style metrics with results and create pre/post splits."""
    merged = style_df.merge(results_df[["Season", "points"]], on="Season", how="left")
    merged = merged.dropna(subset=["points"])
    merged["points_binary"] = (merged["points"] >= 85).astype(int)

    pre_data = merged[merged["season_year"] <= 2021]
    post_data = merged[merged["season_year"] >= 2022]

    return pre_data, post_data


def train_and_explain_rf(X: pd.DataFrame, y: pd.Series) -> tuple[RandomForestClassifier, np.ndarray]:
    """Train RF model."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X_scaled, y)
    
    return model, model.feature_importances_


def plot_feature_importance_comparison(pre_imp, post_imp, feature_names, output_path: Path) -> None:
    """Compare feature importance before and after Haaland."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    sorted_idx_pre = np.argsort(pre_imp)
    axes[0].barh(np.array(feature_names)[sorted_idx_pre], pre_imp[sorted_idx_pre], color="#3949ab")
    axes[0].set_title("Pre-Haaland (2016-2021)\nFeature Importance", fontweight="bold")
    axes[0].set_xlabel("Importance Score")
    
    sorted_idx_post = np.argsort(post_imp)
    axes[1].barh(np.array(feature_names)[sorted_idx_post], post_imp[sorted_idx_post], color="#ff006e")
    axes[1].set_title("Post-Haaland (2022-2024)\nFeature Importance", fontweight="bold")
    axes[1].set_xlabel("Importance Score")
    
    fig.suptitle("Man City Winning Formula: Feature Importance Shift", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    style_df = load_mancity_with_results(STYLE_CSV)
    results_df = load_team_results_points()
    
    print(f"Loaded {len(style_df)} Man City seasons from style metrics")
    print(f"Loaded {len(results_df)} seasons with result points")
    
    if results_df.empty:
        print("ERROR: No match results data found.")
        return
    
    pre_data, post_data = prepare_rf_data(style_df, results_df)
    
    print(f"Pre-Haaland samples: {len(pre_data)}")
    print(f"Post-Haaland samples: {len(post_data)}")
    
    if len(pre_data) < 3 or len(post_data) < 3:
        print("ERROR: Insufficient samples for model training.")
        return
    
    X_pre = pre_data[RF_FEATURES].fillna(0)
    y_pre = pre_data["points_binary"]
    
    X_post = post_data[RF_FEATURES].fillna(0)
    y_post = post_data["points_binary"]
    
    print("\nTraining Random Forest models...")
    pre_model, pre_imp = train_and_explain_rf(X_pre, y_pre)
    post_model, post_imp = train_and_explain_rf(X_post, y_post)
    
    plot_feature_importance_comparison(pre_imp, post_imp, RF_FEATURES, OUTPUT_DIR / "haaland_rf_feature_importance_comparison.png")
    
    results_csv = OUTPUT_DIR / "haaland_rf_feature_importance.csv"
    results_df_out = pd.DataFrame({
        "Feature": RF_FEATURES,
        "Pre_Importance": pre_imp,
        "Post_Importance": post_imp,
        "Change": post_imp - pre_imp,
        "Change_%": (post_imp - pre_imp) / (pre_imp + 1e-6) * 100.0
    }).sort_values("Change_%", ascending=False)
    results_df_out.to_csv(results_csv, index=False)
    print(f"Saved: {results_csv}")
    print("\nFeature Importance Changes:")
    print(results_df_out.to_string(index=False))


if __name__ == "__main__":
    main()
