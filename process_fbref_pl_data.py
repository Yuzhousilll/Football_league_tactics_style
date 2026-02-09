#!/usr/bin/env python3
"""Build cleaned CSV outputs from FBref Premier League season data."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

LEADER_METRICS = [
    ("最佳射手", "goals.csv"),
    ("每90min进球榜", "goals_90.csv"),
    ("助攻王", "assists.csv"),
    ("每90min助攻榜", "assists_90.csv"),
    ("造进球数(进球+助攻)", "goals_assists.csv"),
    ("每90min造进球榜", "goals_assists_90.csv"),
    ("制造点球数", "penalty_kicks_made.csv"),
    ("无点球进球数", "non_penalty_goals.csv"),
    ("射门数", "shots_total.csv"),
    ("每90min射门数", "shots_total_90.csv"),
    ("射正次数", "shots_on_target.csv"),
    ("每90min射正次数", "shots_on_target_90.csv"),
    ("进球/射正", "goals_shot_on_target.csv"),
    ("传中次数", "crosses.csv"),
    ("黄牌数", "yellow_cards.csv"),
    ("红牌数", "red_cards.csv"),
    ("犯规数", "fouls_committed.csv"),
    ("造犯规数", "fouls_drawn.csv"),
    ("成功抢断", "tackles_won.csv"),
    ("拦截", "interceptions.csv"),
    ("最多零封门将", "clean_sheets.csv"),
    ("零封率", "clean_sheet_percentage.csv"),
    ("扑救数", "saves.csv"),
    ("扑救成功率", "save_percentage.csv"),
    ("每90min被进球数", "goals_against_90.csv"),
]


def _split_player_team(value: str) -> tuple[str, str]:
    if pd.isna(value):
        return "", ""
    cleaned = str(value).replace("\xa0", " ").strip()
    parts = re.split(r"\s*•\s*", cleaned, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return cleaned, ""


def build_top_leaders(input_dir: Path) -> pd.DataFrame:
    frames = []
    for metric, filename in LEADER_METRICS:
        path = input_dir / filename
        if not path.exists():
            frames.append(
                pd.DataFrame(
                    [
                        {
                            "metric": metric,
                            "rank": pd.NA,
                            "player": pd.NA,
                            "squad": pd.NA,
                            "value": pd.NA,
                        }
                    ]
                )
            )
            continue
        df = pd.read_csv(path)
        if df.shape[1] < 3:
            raise ValueError(f"Unexpected leaderboard format: {path}")
        df = df.rename(columns={df.columns[0]: "rank", df.columns[1]: "player_team", df.columns[2]: "value"})
        df["rank"] = pd.to_numeric(df["rank"], errors="coerce").ffill().astype("Int64")
        players = df["player_team"].apply(_split_player_team)
        df["player"] = players.map(lambda item: item[0])
        df["squad"] = players.map(lambda item: item[1])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["metric"] = metric
        frames.append(df[["metric", "rank", "player", "squad", "value"]])

    if not frames:
        return pd.DataFrame(columns=["metric", "rank", "player", "squad", "value"])
    return pd.concat(frames, ignore_index=True)


def _safe_select(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return df.reindex(columns=columns)


def _find_results_overall(input_dir: Path) -> Path:
    candidates = sorted(input_dir.glob("results*_overall.csv"))
    if not candidates:
        raise FileNotFoundError(f"Missing results overall table in {input_dir}")
    return candidates[0]


def build_general_stats(input_dir: Path) -> pd.DataFrame:
    standings = pd.read_csv(_find_results_overall(input_dir))
    standings = _safe_select(
        standings, ["Squad", "W", "D", "L", "GF", "GA", "GD", "Pts", "Pts/MP", "Attendance"]
    )

    standard = pd.read_csv(input_dir / "stats_squads_standard_for.csv", header=1)
    standard = _safe_select(
        standard,
        [
            "Squad",
            "# Pl",
            "Age",
            "Poss",
            "Gls",
            "Ast",
            "G+A",
            "G-PK",
            "PK",
            "PKatt",
            "CrdY",
            "CrdR",
        ],
    ).rename(columns={"# Pl": "Std_#Pl"})

    goalkeeping = pd.read_csv(input_dir / "stats_squads_keeper_for.csv", header=1)
    goalkeeping = _safe_select(
        goalkeeping,
        ["Squad", "# Pl", "GA", "SoTA", "Saves", "Save%", "CS", "CS%"],
    ).rename(columns={"# Pl": "GK_#Pl"})

    shooting = pd.read_csv(input_dir / "stats_squads_shooting_for.csv", header=1)
    shooting = _safe_select(shooting, ["Squad", "Sh", "SoT", "SoT%", "G/Sh", "G/SoT"])

    misc = pd.read_csv(input_dir / "stats_squads_misc_for.csv", header=1)
    misc = _safe_select(misc, ["Squad", "Fls", "Fld", "Off", "Crs", "Int", "TklW", "PKwon", "PKcon", "OG"])

    merged = standings.merge(standard, on="Squad", how="left")
    merged = merged.merge(goalkeeping, on="Squad", how="left")
    merged = merged.merge(shooting, on="Squad", how="left")
    merged = merged.merge(misc, on="Squad", how="left")
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Build cleaned FBref PL CSVs")
    parser.add_argument(
        "--input-dir",
        default="data/fbref_pl_2017_2018",
        help="Directory containing scraped FBref CSVs",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (defaults to input dir)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    top_leaders = build_top_leaders(input_dir)
    top_leaders.to_csv(output_dir / "top_leaders.csv", index=False, na_rep="null")

    general_stats = build_general_stats(input_dir)
    general_stats.to_csv(output_dir / "general_stats.csv", index=False, na_rep="null")

    print(f"Saved top_leaders.csv and general_stats.csv to {output_dir}")


if __name__ == "__main__":
    main()
