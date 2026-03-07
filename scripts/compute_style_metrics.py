#!/usr/bin/env python3
import argparse
import os
import re
from glob import glob
from typing import List

import pandas as pd

DEFAULT_SEASON_START = "2016-2017"
DEFAULT_SEASON_END = "2024-2025"


def flatten_multiindex_columns(columns: pd.MultiIndex) -> List[str]:
    new_cols = []
    counts = {}
    for lvl0, lvl1 in columns:
        base = lvl1 if lvl1 and not str(lvl1).startswith("Unnamed") else lvl0
        if str(lvl0).startswith("Penalty") and base == "Save%":
            base = "Save%_pk"
        if base in counts:
            counts[base] += 1
            base = f"{base}_{counts[base]}"
        else:
            counts[base] = 1
        new_cols.append(base)
    return new_cols


def read_misc(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, header=[0, 1])
    df.columns = flatten_multiindex_columns(df.columns)
    return df


def read_keeper(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, header=[0, 1])
    df.columns = flatten_multiindex_columns(df.columns)
    return df


def safe_divide(numerator, denominator):
    return numerator / denominator.replace({0: pd.NA})


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


def compute_metrics(season_dir: str) -> pd.DataFrame:
    general_path = os.path.join(season_dir, "general_stats.csv")
    misc_path = os.path.join(season_dir, "stats_squads_misc_for.csv")
    keeper_path = os.path.join(season_dir, "stats_squads_keeper_for.csv")
    results_candidates = sorted(glob(os.path.join(season_dir, "results*_overall.csv")))

    if not (os.path.exists(general_path) and os.path.exists(misc_path) and os.path.exists(keeper_path)):
        return pd.DataFrame()
    if not results_candidates:
        return pd.DataFrame()

    results_path = results_candidates[0]

    general = pd.read_csv(general_path)
    misc = read_misc(misc_path)
    keeper = read_keeper(keeper_path)
    results = pd.read_csv(results_path)

    general_cols = ["Squad", "Age", "Ast", "Gls", "Sh", "SoT", "PK"]
    misc_cols = ["Squad", "CrdY", "CrdR", "Fls", "Fld", "Off", "Crs", "Int", "TklW", "PKwon", "# Pl"]
    keeper_cols = ["Squad", "CS", "Save%", "SoTA"]
    results_cols = ["Squad", "MP", "GF", "GA"]

    general = general[[c for c in general_cols if c in general.columns]].copy()
    misc = misc[[c for c in misc_cols if c in misc.columns]].copy()
    keeper = keeper[[c for c in keeper_cols if c in keeper.columns]].copy()
    results = results[[c for c in results_cols if c in results.columns]].copy()

    combined = results.merge(general, on="Squad", how="left")
    combined = combined.merge(misc, on="Squad", how="left")
    combined = combined.merge(keeper, on="Squad", how="left")

    for col in combined.columns:
        if col == "Squad":
            continue
        combined[col] = pd.to_numeric(combined[col], errors="coerce")

    metrics = pd.DataFrame()
    metrics["Squad"] = combined["Squad"]
    metrics["shots_per_match"] = safe_divide(combined.get("Sh"), combined.get("MP"))
    metrics["shots_on_target_per_match"] = safe_divide(combined.get("SoT"), combined.get("MP"))
    metrics["fouls_per_match"] = safe_divide(combined.get("Fls"), combined.get("MP"))
    metrics["offsides_per_match"] = safe_divide(combined.get("Off"), combined.get("MP"))
    metrics["cards_per_match"] = safe_divide(combined.get("CrdY") + combined.get("CrdR"), combined.get("MP"))
    metrics["goals_per_match"] = safe_divide(combined.get("GF"), combined.get("MP"))
    metrics["assists_per_match"] = safe_divide(combined.get("Ast"), combined.get("MP"))
    metrics["goals_per_shot"] = safe_divide(combined.get("Gls"), combined.get("Sh"))
    metrics["goals_per_sot"] = safe_divide(combined.get("Gls"), combined.get("SoT"))
    metrics["cross_volume_per_match"] = safe_divide(combined.get("Crs"), combined.get("MP"))
    metrics["cross_share_of_touches"] = safe_divide(combined.get("Crs"), combined.get("Sh") + combined.get("Crs"))
    metrics["penalty_goal_share"] = safe_divide(combined.get("PK"), combined.get("GF"))
    metrics["penalties_won_per_match"] = safe_divide(combined.get("PKwon"), combined.get("MP"))
    metrics["offsides_to_shots_ratio"] = safe_divide(combined.get("Off"), combined.get("Sh"))
    metrics["goals_against_per_match"] = safe_divide(combined.get("GA"), combined.get("MP"))
    metrics["clean_sheet_pct"] = safe_divide(combined.get("CS"), combined.get("MP"))
    metrics["tackles_won_per_match"] = safe_divide(combined.get("TklW"), combined.get("MP"))
    metrics["interceptions_per_match"] = safe_divide(combined.get("Int"), combined.get("MP"))
    metrics["defensive_actions_per_match"] = safe_divide(combined.get("TklW") + combined.get("Int"), combined.get("MP"))
    metrics["save_pct"] = combined.get("Save%")
    metrics["shots_on_target_against_per_match"] = safe_divide(combined.get("SoTA"), combined.get("MP"))
    metrics["red_cards_per_match"] = safe_divide(combined.get("CrdR"), combined.get("MP"))
    metrics["fouls_drawn_per_match"] = safe_divide(combined.get("Fld"), combined.get("MP"))
    metrics["avg_age"] = combined.get("Age")
    metrics["players_used"] = combined.get("# Pl")

    season = os.path.basename(season_dir).replace("fbref_pl_", "")
    metrics.insert(0, "Season", season)

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Compute style trend metrics for selected seasons.")
    parser.add_argument("--data-dir", default="data", help="Base data directory (default: data).")
    parser.add_argument(
        "--output",
        default="data/derived/style_metrics_all.csv",
        help="Output CSV path (default: data/derived/style_metrics_all.csv).",
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
    args = parser.parse_args()

    season_dirs = sorted(glob(os.path.join(args.data_dir, "fbref_pl_*")))
    if not season_dirs:
        raise SystemExit("No season folders found under data.")

    all_metrics = []
    for season_dir in season_dirs:
        season_label = os.path.basename(season_dir).replace("fbref_pl_", "")
        if not season_in_range(season_label, args.season_start, args.season_end):
            continue
        season_metrics = compute_metrics(season_dir)
        if not season_metrics.empty:
            all_metrics.append(season_metrics)

    if not all_metrics:
        raise SystemExit("No metrics computed. Check season range and source CSV files.")

    output_df = pd.concat(all_metrics, ignore_index=True)
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    output_df.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
