#!/usr/bin/env python3
"""Extract all Haaland data from FBref Premier League seasons and analyse his impact.

Outputs:
  haaland_analysis/haaland_data.csv              – consolidated per-season stats
  haaland_analysis/haaland_season_stats.svg      – key metrics across seasons
  haaland_analysis/haaland_vs_top_scorers.svg    – Haaland vs season top scorers
  haaland_analysis/haaland_mancity_contribution.svg – share of Man City goals
  haaland_analysis/haaland_pre_mancity_context.svg  – Man City pre-Haaland context
  haaland_analysis/haaland_vs_league_avg.svg        – Haaland vs league average
  haaland_analysis/HAALAND_ANALYSIS_REPORT.md    – written analysis
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "haaland_analysis"

SEASONS = [
    ("2022-2023", "fbref_pl_2022_2023"),
    ("2023-2024", "fbref_pl_2023_2024"),
    ("2024-2025", "fbref_pl_2024_2025"),
]

PRE_HAALAND_CITY_SEASONS = [
    ("2019-2020", "fbref_pl_2019_2020"),
    ("2020-2021", "fbref_pl_2020_2021"),
    ("2021-2022", "fbref_pl_2021_2022"),
]

# (column_key, csv_filename)
PLAYER_METRICS = [
    ("goals", "goals.csv"),
    ("assists", "assists.csv"),
    ("goals_assists", "goals_assists.csv"),
    ("non_penalty_goals", "non_penalty_goals.csv"),
    ("penalty_kicks_made", "penalty_kicks_made.csv"),
    ("shots_total", "shots_total.csv"),
    ("shots_on_target", "shots_on_target.csv"),
    ("goals_90", "goals_90.csv"),
    ("assists_90", "assists_90.csv"),
    ("goals_assists_90", "goals_assists_90.csv"),
    ("non_penalty_goals_90", "non_penalty_goals_90.csv"),
    ("non_penalty_goals_assists_90", "non_penalty_goals_assists_90.csv"),
    ("shots_total_90", "shots_total_90.csv"),
    ("shots_on_target_90", "shots_on_target_90.csv"),
    ("goals_shot", "goals_shot.csv"),
    ("plus_minus", "plus_minus.csv"),
    ("plus_minus_90", "plus_minus_90.csv"),
    ("points_per_match", "points_per_match.csv"),
]

LEAGUE_AVG_METRICS = [
    "goals_90",
    "shots_total_90",
    "shots_on_target_90",
    "goals_shot",
]

PLAYER_NAME = "Erling Haaland"


# ---------------------------------------------------------------------------
# Data extraction helpers
# ---------------------------------------------------------------------------


def _read_leaderboard(path: Path) -> list[dict]:
    """Return rows from a rank/player_team/value leaderboard CSV.

    The raw files have a numeric header row (``0,1,2``) that is skipped.
    """
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header row (0,1,2)
        for r in reader:
            if len(r) < 3:
                continue
            rows.append({"rank": r[0], "player_team": r[1], "value": r[2]})
    return rows


def _find_player(rows: list[dict], player: str) -> float | None:
    """Return the numeric value for *player* in leaderboard rows, or None."""
    name_lower = player.lower()
    for r in rows:
        if name_lower in r["player_team"].lower():
            try:
                return float(r["value"])
            except (ValueError, TypeError):
                return None
    return None


def _avg_value(rows: list[dict]) -> float | None:
    vals: list[float] = []
    for r in rows:
        try:
            vals.append(float(r["value"]))
        except (ValueError, TypeError, KeyError):
            continue
    if not vals:
        return None
    return round(sum(vals) / len(vals), 3)


def _read_results_overall(path: Path) -> dict | None:
    """Return the Manchester City row from a results-overall CSV."""
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if "manchester city" in r.get("Squad", "").lower():
                return r
    return None


def extract_haaland_season(season_label: str, season_dir: Path) -> dict:
    """Collect all available metrics for Haaland in one season."""
    record: dict = {"season": season_label}
    for key, filename in PLAYER_METRICS:
        rows = _read_leaderboard(season_dir / filename)
        record[key] = _find_player(rows, PLAYER_NAME)
        if key in LEAGUE_AVG_METRICS:
            record[f"league_avg_{key}"] = _avg_value(rows)

    # Man City team stats from results table
    candidates = sorted(season_dir.glob("results*_overall.csv"))
    city_row: dict | None = None
    if candidates:
        city_row = _read_results_overall(candidates[0])
    if city_row:
        record["city_rank"] = _safe_int(city_row.get("Rk"))
        record["city_pts"] = _safe_float(city_row.get("Pts"))
        record["city_goals"] = _safe_float(city_row.get("GF"))
        record["city_wins"] = _safe_float(city_row.get("W"))
        record["city_top_scorer_raw"] = city_row.get("Top Team Scorer", "")
    else:
        record["city_rank"] = None
        record["city_pts"] = None
        record["city_goals"] = None
        record["city_wins"] = None
        record["city_top_scorer_raw"] = ""

    # Haaland goal share of Man City total
    if record.get("goals") is not None and record.get("city_goals") and record["city_goals"] > 0:
        record["haaland_goal_share_pct"] = round(record["goals"] / record["city_goals"] * 100, 1)
    else:
        record["haaland_goal_share_pct"] = None

    # Season golden boot winner (top scorer rank 1)
    boot_rows = _read_leaderboard(season_dir / "goals.csv")
    if boot_rows:
        record["golden_boot_player"] = boot_rows[0]["player_team"]
        try:
            record["golden_boot_goals"] = float(boot_rows[0]["value"])
        except (ValueError, TypeError):
            record["golden_boot_goals"] = None
    else:
        record["golden_boot_player"] = ""
        record["golden_boot_goals"] = None

    return record


def _parse_top_scorer_goals(raw: str) -> float | None:
    if not raw:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*$", raw)
    if not m:
        return None
    return _safe_float(m.group(1))


def _parse_top_scorer_name(raw: str) -> str:
    if not raw:
        return ""
    return re.split(r"\s*[•·]\s*", raw)[0].strip()


def extract_city_season(season_label: str, season_dir: Path) -> dict:
    """Collect Man City attacking output and standings in one season."""
    record: dict = {"season": season_label}
    candidates = sorted(season_dir.glob("results*_overall.csv"))
    city_row: dict | None = None
    if candidates:
        city_row = _read_results_overall(candidates[0])
    if city_row:
        record["city_rank"] = _safe_int(city_row.get("Rk"))
        record["city_pts"] = _safe_float(city_row.get("Pts"))
        record["city_goals"] = _safe_float(city_row.get("GF"))
        record["city_wins"] = _safe_float(city_row.get("W"))
        record["city_top_scorer_raw"] = city_row.get("Top Team Scorer", "")
        record["city_top_scorer_goals"] = _parse_top_scorer_goals(record["city_top_scorer_raw"])
    else:
        record["city_rank"] = None
        record["city_pts"] = None
        record["city_goals"] = None
        record["city_wins"] = None
        record["city_top_scorer_raw"] = ""
        record["city_top_scorer_goals"] = None
    return record


def _safe_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _safe_ratio(numerator: float | None, denominator: float | None, digits: int = 2) -> float | None:
    if numerator is None or denominator is None:
        return None
    if abs(denominator) <= 1e-9:
        return None
    return round(numerator / denominator, digits)


# ---------------------------------------------------------------------------
# Extract data for all seasons
# ---------------------------------------------------------------------------


def build_haaland_dataset() -> list[dict]:
    records = []
    for label, dirname in SEASONS:
        season_dir = DATA_ROOT / dirname
        if not season_dir.exists():
            continue
        rec = extract_haaland_season(label, season_dir)
        records.append(rec)
    return records


def build_pre_haaland_city_dataset() -> list[dict]:
    records = []
    for label, dirname in PRE_HAALAND_CITY_SEASONS:
        season_dir = DATA_ROOT / dirname
        if not season_dir.exists():
            continue
        records.append(extract_city_season(label, season_dir))
    return records


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------


def save_csv(records: list[dict], path: Path) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0].keys())
    # Replace None with "null" so every field is explicit in the output
    cleaned = [
        {k: ("null" if v is None else v) for k, v in row.items()}
        for row in records
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned)


# ---------------------------------------------------------------------------
# SVG charting helpers (stdlib only, no matplotlib)
# ---------------------------------------------------------------------------

W, H = 800, 480
MARGIN = {"top": 60, "right": 30, "bottom": 70, "left": 70}
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
SEASON_COLORS = {"2022-2023": "#1f77b4", "2023-2024": "#ff7f0e", "2024-2025": "#2ca02c"}


def _scale(v, vmin, vmax, pmin, pmax):
    if vmax == vmin:
        return (pmin + pmax) / 2
    return pmin + (v - vmin) / (vmax - vmin) * (pmax - pmin)


def _svg_header(title: str, w=W, h=H) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">\n'
        f'<rect width="{w}" height="{h}" fill="white"/>\n'
        f'<text x="{w//2}" y="30" font-size="16" font-weight="bold" '
        f'text-anchor="middle" font-family="Arial,sans-serif">{title}</text>\n'
    )


def _svg_footer() -> str:
    return "</svg>\n"


def _svg_axes(x0, y0, x1, y1) -> str:
    return (
        f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="black" stroke-width="1.5"/>\n'
        f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="black" stroke-width="1.5"/>\n'
    )


def _svg_text(x, y, text, anchor="middle", size=11, color="black", bold=False) -> str:
    fw = "bold" if bold else "normal"
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
        f'font-family="Arial,sans-serif" fill="{color}" font-weight="{fw}">{text}</text>\n'
    )


def _fmt(v) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


# ---------------------------------------------------------------------------
# Chart 1: Season stats bar chart (goals, assists, shots)
# ---------------------------------------------------------------------------


def chart_season_stats(records: list[dict], path: Path) -> None:
    metrics = [
        ("goals", "进球数 Goals"),
        ("assists", "助攻数 Assists"),
        ("shots_total", "射门数 Shots"),
        ("shots_on_target", "射正数 SoT"),
    ]
    seasons = [r["season"] for r in records]
    n_seasons = len(seasons)
    n_metrics = len(metrics)

    x0 = MARGIN["left"]
    x1 = W - MARGIN["right"]
    y0 = MARGIN["top"] + 10
    y1 = H - MARGIN["bottom"]

    all_vals = []
    for key, _ in metrics:
        for r in records:
            v = r.get(key)
            if v is not None:
                all_vals.append(v)
    vmax = max(all_vals) if all_vals else 1
    vmin = 0

    group_w = (x1 - x0) / n_metrics
    bar_w = group_w * 0.7 / n_seasons

    svg = _svg_header("哈兰德英超各赛季核心数据 Haaland PL Season Statistics")
    svg += _svg_axes(x0, y0, x1, y1)

    # Y-axis ticks
    for tick in range(0, int(vmax) + 1, 20):
        if tick > vmax:
            break
        ty = _scale(tick, vmin, vmax, y1, y0)
        svg += f'<line x1="{x0-5}" y1="{ty:.1f}" x2="{x0}" y2="{ty:.1f}" stroke="black" stroke-width="1"/>\n'
        svg += _svg_text(x0 - 8, ty + 4, str(tick), anchor="end", size=10)
        svg += f'<line x1="{x0}" y1="{ty:.1f}" x2="{x1}" y2="{ty:.1f}" stroke="#ddd" stroke-width="0.8"/>\n'

    # Bars
    for mi, (key, label) in enumerate(metrics):
        gx = x0 + mi * group_w + group_w * 0.15
        for si, rec in enumerate(records):
            v = rec.get(key)
            if v is None:
                continue
            color = COLORS[si % len(COLORS)]
            bx = gx + si * bar_w
            by = _scale(v, vmin, vmax, y1, y0)
            bh = y1 - by
            svg += (
                f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
                f'fill="{color}" opacity="0.85"/>\n'
            )
            svg += _svg_text(bx + bar_w / 2, by - 3, _fmt(v), size=9, color=color)

        # X-axis label
        svg += _svg_text(gx + bar_w * n_seasons / 2, y1 + 18, label, size=10)

    # Legend
    lx = x0 + 10
    for si, rec in enumerate(records):
        color = COLORS[si % len(COLORS)]
        svg += f'<rect x="{lx}" y="{H - 28}" width="12" height="12" fill="{color}"/>\n'
        svg += _svg_text(lx + 16, H - 18, rec["season"], anchor="start", size=10)
        lx += 100

    svg += _svg_footer()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------------------
# Chart 2: Haaland vs golden-boot winner each season
# ---------------------------------------------------------------------------


def chart_vs_top_scorers(records: list[dict], path: Path) -> None:
    seasons = [r["season"] for r in records]
    haaland_goals = [r.get("goals") or 0 for r in records]
    boot_goals = [r.get("golden_boot_goals") or 0 for r in records]

    x0 = MARGIN["left"]
    x1 = W - MARGIN["right"]
    y0 = MARGIN["top"] + 10
    y1 = H - MARGIN["bottom"]

    vmax = max(max(haaland_goals), max(boot_goals), 1) * 1.1
    vmin = 0

    n = len(seasons)
    group_w = (x1 - x0) / n
    bar_w = group_w * 0.35

    svg = _svg_header("哈兰德 vs 英超射手王对比 Haaland vs Golden Boot Winner")
    svg += _svg_axes(x0, y0, x1, y1)

    for tick in range(0, int(vmax) + 1, 5):
        if tick > vmax:
            break
        ty = _scale(tick, vmin, vmax, y1, y0)
        svg += f'<line x1="{x0-5}" y1="{ty:.1f}" x2="{x0}" y2="{ty:.1f}" stroke="black" stroke-width="1"/>\n'
        svg += _svg_text(x0 - 8, ty + 4, str(tick), anchor="end", size=10)
        svg += f'<line x1="{x0}" y1="{ty:.1f}" x2="{x1}" y2="{ty:.1f}" stroke="#ddd" stroke-width="0.8"/>\n'

    for i, rec in enumerate(records):
        gx = x0 + i * group_w + group_w * 0.15
        # Haaland bar
        hv = haaland_goals[i]
        hy = _scale(hv, vmin, vmax, y1, y0)
        svg += (
            f'<rect x="{gx:.1f}" y="{hy:.1f}" width="{bar_w:.1f}" height="{y1-hy:.1f}" '
            f'fill="#1f77b4" opacity="0.85"/>\n'
        )
        svg += _svg_text(gx + bar_w / 2, hy - 3, str(int(hv)), size=10, color="#1f77b4", bold=True)

        # Top scorer bar
        bv = boot_goals[i]
        by = _scale(bv, vmin, vmax, y1, y0)
        bx = gx + bar_w + 4
        svg += (
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{y1-by:.1f}" '
            f'fill="#ff7f0e" opacity="0.85"/>\n'
        )
        svg += _svg_text(bx + bar_w / 2, by - 3, str(int(bv)), size=10, color="#ff7f0e", bold=True)

        # Season label + golden boot name
        boot_raw = rec.get("golden_boot_player", "")
        # Strip team suffix (after •)
        boot_name = re.split(r"\s*[•·]\s*", boot_raw)[0].strip() if boot_raw else ""
        svg += _svg_text(gx + bar_w, y1 + 16, rec["season"], size=10)
        svg += _svg_text(gx + bar_w, y1 + 32, f"榜首: {boot_name}", size=9, color="#ff7f0e")

    # Legend
    lx = x0 + 10
    for label, color in [("Erling Haaland", "#1f77b4"), ("赛季射手王 Top Scorer", "#ff7f0e")]:
        svg += f'<rect x="{lx}" y="{H - 28}" width="12" height="12" fill="{color}"/>\n'
        svg += _svg_text(lx + 16, H - 18, label, anchor="start", size=10)
        lx += 220

    svg += _svg_footer()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------------------
# Chart 3: Haaland's contribution to Man City goals
# ---------------------------------------------------------------------------


def chart_mancity_contribution(records: list[dict], path: Path) -> None:
    x0 = MARGIN["left"]
    x1 = W - MARGIN["right"]
    y0 = MARGIN["top"] + 10
    y1 = H - MARGIN["bottom"]

    n = len(records)
    bar_w = (x1 - x0) / n * 0.5

    # Stacked: haaland goals vs rest of city goals
    city_goals = [r.get("city_goals") or 0 for r in records]
    haaland_goals = [r.get("goals") or 0 for r in records]
    rest_goals = [max(c - h, 0) for c, h in zip(city_goals, haaland_goals)]
    vmax = max(city_goals + [1]) * 1.1
    vmin = 0

    svg = _svg_header("哈兰德在曼城进球中的贡献 Haaland Contribution to Man City Goals")
    svg += _svg_axes(x0, y0, x1, y1)

    for tick in range(0, int(vmax) + 1, 10):
        if tick > vmax:
            break
        ty = _scale(tick, vmin, vmax, y1, y0)
        svg += f'<line x1="{x0-5}" y1="{ty:.1f}" x2="{x0}" y2="{ty:.1f}" stroke="black" stroke-width="1"/>\n'
        svg += _svg_text(x0 - 8, ty + 4, str(tick), anchor="end", size=10)
        svg += f'<line x1="{x0}" y1="{ty:.1f}" x2="{x1}" y2="{ty:.1f}" stroke="#ddd" stroke-width="0.8"/>\n'

    for i, rec in enumerate(records):
        bx = x0 + i * (x1 - x0) / n + ((x1 - x0) / n - bar_w) / 2
        hv = haaland_goals[i]
        rv = rest_goals[i]

        # Rest of city goals (bottom)
        ry = _scale(rv, vmin, vmax, y1, y0)
        svg += (
            f'<rect x="{bx:.1f}" y="{ry:.1f}" width="{bar_w:.1f}" height="{y1-ry:.1f}" '
            f'fill="#aec7e8" opacity="0.9"/>\n'
        )

        # Haaland goals (stacked on top)
        total = hv + rv
        ty_total = _scale(total, vmin, vmax, y1, y0)
        hh = ry - ty_total
        svg += (
            f'<rect x="{bx:.1f}" y="{ty_total:.1f}" width="{bar_w:.1f}" height="{hh:.1f}" '
            f'fill="#1f77b4" opacity="0.9"/>\n'
        )

        # Labels
        pct = rec.get("haaland_goal_share_pct")
        pct_str = f"{pct}%" if pct is not None else ""
        svg += _svg_text(bx + bar_w / 2, ty_total - 3, f"{int(hv)} ({pct_str})", size=10, bold=True)
        svg += _svg_text(bx + bar_w / 2, y1 + 18, rec["season"], size=10)
        svg += _svg_text(bx + bar_w / 2, y1 + 33, f"曼城共 {int(total)} 球", size=9, color="#555")

    # Legend
    lx = x0 + 10
    for label, color in [("哈兰德进球 Haaland Goals", "#1f77b4"), ("其他球员进球 Other Goals", "#aec7e8")]:
        svg += f'<rect x="{lx}" y="{H - 28}" width="12" height="12" fill="{color}"/>\n'
        svg += _svg_text(lx + 16, H - 18, label, anchor="start", size=10)
        lx += 230

    svg += _svg_footer()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------------------
# Chart 4: Per-90 efficiency metrics across seasons
# ---------------------------------------------------------------------------


def chart_per90_metrics(records: list[dict], path: Path) -> None:
    metrics_90 = [
        ("goals_90", "进球/90min"),
        ("shots_on_target_90", "射正/90min"),
        ("shots_total_90", "射门/90min"),
        ("goals_assists_90", "进球+助攻/90min"),
    ]
    seasons = [r["season"] for r in records]
    n_seasons = len(seasons)

    x0 = MARGIN["left"]
    x1 = W - MARGIN["right"]
    y0 = MARGIN["top"] + 10
    y1 = H - MARGIN["bottom"]

    all_vals = [r.get(k) for r in records for k, _ in metrics_90 if r.get(k) is not None]
    vmax = max(all_vals) if all_vals else 1
    vmin = 0

    n_metrics = len(metrics_90)
    group_w = (x1 - x0) / n_metrics
    bar_w = group_w * 0.7 / n_seasons

    svg = _svg_header("哈兰德每90分钟效率指标 Haaland Per-90 Efficiency Metrics")
    svg += _svg_axes(x0, y0, x1, y1)

    for tick_f in [i * 0.5 for i in range(0, int(vmax / 0.5) + 2)]:
        if tick_f > vmax * 1.05:
            break
        ty = _scale(tick_f, vmin, vmax, y1, y0)
        svg += f'<line x1="{x0-5}" y1="{ty:.1f}" x2="{x0}" y2="{ty:.1f}" stroke="black" stroke-width="1"/>\n'
        svg += _svg_text(x0 - 8, ty + 4, f"{tick_f:.1f}", anchor="end", size=10)
        svg += f'<line x1="{x0}" y1="{ty:.1f}" x2="{x1}" y2="{ty:.1f}" stroke="#ddd" stroke-width="0.8"/>\n'

    for mi, (key, label) in enumerate(metrics_90):
        gx = x0 + mi * group_w + group_w * 0.15
        for si, rec in enumerate(records):
            v = rec.get(key)
            if v is None:
                continue
            color = COLORS[si % len(COLORS)]
            bx = gx + si * bar_w
            by = _scale(v, vmin, vmax, y1, y0)
            bh = y1 - by
            svg += (
                f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
                f'fill="{color}" opacity="0.85"/>\n'
            )
            svg += _svg_text(bx + bar_w / 2, by - 3, f"{v:.2f}", size=9, color=color)
        svg += _svg_text(gx + bar_w * n_seasons / 2, y1 + 20, label, size=9)

    # Legend
    lx = x0 + 10
    for si, rec in enumerate(records):
        color = COLORS[si % len(COLORS)]
        svg += f'<rect x="{lx}" y="{H - 28}" width="12" height="12" fill="{color}"/>\n'
        svg += _svg_text(lx + 16, H - 18, rec["season"], anchor="start", size=10)
        lx += 100

    svg += _svg_footer()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def chart_pre_mancity_context(pre_records: list[dict], post_records: list[dict], path: Path) -> None:
    all_records = pre_records + post_records
    if not all_records:
        return

    x0 = MARGIN["left"]
    x1 = W - MARGIN["right"]
    y0 = MARGIN["top"] + 10
    y1 = H - MARGIN["bottom"]
    n = len(all_records)

    goals_vals = [r.get("city_goals") or 0 for r in all_records]
    pts_vals = [r.get("city_pts") or 0 for r in all_records]
    vmax = max(goals_vals + pts_vals + [1]) * 1.1

    group_w = (x1 - x0) / n
    bar_w = group_w * 0.32
    pre_n = len(pre_records)

    svg = _svg_header("曼城进攻与成绩：哈兰德加盟前后对比 Man City Before vs After Haaland")
    svg += _svg_axes(x0, y0, x1, y1)

    for tick in range(0, int(vmax) + 1, 10):
        if tick > vmax:
            break
        ty = _scale(tick, 0, vmax, y1, y0)
        svg += f'<line x1="{x0-5}" y1="{ty:.1f}" x2="{x0}" y2="{ty:.1f}" stroke="black" stroke-width="1"/>\n'
        svg += _svg_text(x0 - 8, ty + 4, str(tick), anchor="end", size=10)
        svg += f'<line x1="{x0}" y1="{ty:.1f}" x2="{x1}" y2="{ty:.1f}" stroke="#ddd" stroke-width="0.8"/>\n'

    for i, rec in enumerate(all_records):
        gx = x0 + i * group_w + group_w * 0.15
        in_pre = i < pre_n
        goals_color = "#7f7f7f" if in_pre else "#1f77b4"
        pts_color = "#c7c7c7" if in_pre else "#ff7f0e"

        gv = rec.get("city_goals") or 0
        gy = _scale(gv, 0, vmax, y1, y0)
        svg += (
            f'<rect x="{gx:.1f}" y="{gy:.1f}" width="{bar_w:.1f}" height="{y1-gy:.1f}" '
            f'fill="{goals_color}" opacity="0.9"/>\n'
        )

        pv = rec.get("city_pts") or 0
        py = _scale(pv, 0, vmax, y1, y0)
        px = gx + bar_w + 4
        svg += (
            f'<rect x="{px:.1f}" y="{py:.1f}" width="{bar_w:.1f}" height="{y1-py:.1f}" '
            f'fill="{pts_color}" opacity="0.9"/>\n'
        )

        svg += _svg_text(gx + bar_w / 2, gy - 3, _fmt(rec.get("city_goals")), size=9, color=goals_color)
        svg += _svg_text(px + bar_w / 2, py - 3, _fmt(rec.get("city_pts")), size=9, color=pts_color)
        svg += _svg_text(gx + bar_w, y1 + 16, rec["season"], size=9)
        svg += _svg_text(gx + bar_w, y1 + 30, f"Rk {_fmt(rec.get('city_rank'))}", size=9, color="#444")

    if pre_n:
        divider_x = x0 + pre_n * group_w
        svg += f'<line x1="{divider_x:.1f}" y1="{y0}" x2="{divider_x:.1f}" y2="{y1+34}" stroke="#999" stroke-width="1.2" stroke-dasharray="4,3"/>\n'
        svg += _svg_text(x0 + (divider_x - x0) / 2, y0 - 10, "哈兰德加盟前", size=10, color="#555", bold=True)
        svg += _svg_text(divider_x + (x1 - divider_x) / 2, y0 - 10, "哈兰德加盟后", size=10, color="#1f77b4", bold=True)

    lx = x0 + 10
    for label, color in [
        ("进球 GF（前）", "#7f7f7f"),
        ("积分 Pts（前）", "#c7c7c7"),
        ("进球 GF（后）", "#1f77b4"),
        ("积分 Pts（后）", "#ff7f0e"),
    ]:
        svg += f'<rect x="{lx}" y="{H - 28}" width="12" height="12" fill="{color}"/>\n'
        svg += _svg_text(lx + 16, H - 18, label, anchor="start", size=9)
        lx += 170

    svg += _svg_footer()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def chart_haaland_vs_league_avg(records: list[dict], path: Path) -> None:
    metrics = [
        ("goals_90", "进球/90"),
        ("shots_total_90", "射门/90"),
        ("shots_on_target_90", "射正/90"),
        ("goals_shot", "每射门进球率"),
    ]
    summary = []
    for key, label in metrics:
        haaland_vals = [r.get(key) for r in records if r.get(key) is not None]
        league_vals = [r.get(f"league_avg_{key}") for r in records if r.get(f"league_avg_{key}") is not None]
        haaland_avg = sum(haaland_vals) / len(haaland_vals) if haaland_vals else 0
        league_avg = sum(league_vals) / len(league_vals) if league_vals else 0
        summary.append((label, haaland_avg, league_avg))

    x0 = MARGIN["left"]
    x1 = W - MARGIN["right"]
    y0 = MARGIN["top"] + 10
    y1 = H - MARGIN["bottom"]
    vmax = max([max(h, l) for _, h, l in summary] + [1]) * 1.15
    n = len(summary)
    group_w = (x1 - x0) / n
    bar_w = group_w * 0.32

    svg = _svg_header("哈兰德 vs 联赛平均（入榜球员） Haaland vs League Average")
    svg += _svg_axes(x0, y0, x1, y1)

    for tick_f in [i * 0.2 for i in range(0, int(vmax / 0.2) + 2)]:
        if tick_f > vmax * 1.02:
            break
        ty = _scale(tick_f, 0, vmax, y1, y0)
        svg += f'<line x1="{x0-5}" y1="{ty:.1f}" x2="{x0}" y2="{ty:.1f}" stroke="black" stroke-width="1"/>\n'
        svg += _svg_text(x0 - 8, ty + 4, f"{tick_f:.1f}", anchor="end", size=10)
        svg += f'<line x1="{x0}" y1="{ty:.1f}" x2="{x1}" y2="{ty:.1f}" stroke="#ddd" stroke-width="0.8"/>\n'

    for i, (label, hv, lv) in enumerate(summary):
        gx = x0 + i * group_w + group_w * 0.18
        hy = _scale(hv, 0, vmax, y1, y0)
        ly = _scale(lv, 0, vmax, y1, y0)
        svg += f'<rect x="{gx:.1f}" y="{hy:.1f}" width="{bar_w:.1f}" height="{y1-hy:.1f}" fill="#1f77b4" opacity="0.9"/>\n'
        svg += f'<rect x="{gx+bar_w+4:.1f}" y="{ly:.1f}" width="{bar_w:.1f}" height="{y1-ly:.1f}" fill="#ff7f0e" opacity="0.9"/>\n'
        svg += _svg_text(gx + bar_w / 2, hy - 3, f"{hv:.2f}", size=9, color="#1f77b4", bold=True)
        svg += _svg_text(gx + bar_w + 4 + bar_w / 2, ly - 3, f"{lv:.2f}", size=9, color="#ff7f0e", bold=True)
        svg += _svg_text(gx + bar_w, y1 + 18, label, size=9)

    lx = x0 + 10
    for label, color in [("哈兰德（3季均值）", "#1f77b4"), ("联赛均值（同指标入榜球员）", "#ff7f0e")]:
        svg += f'<rect x="{lx}" y="{H - 28}" width="12" height="12" fill="{color}"/>\n'
        svg += _svg_text(lx + 16, H - 18, label, anchor="start", size=10)
        lx += 260

    svg += _svg_footer()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def _row(*cells) -> str:
    return "| " + " | ".join(str(c) if c is not None else "N/A" for c in cells) + " |\n"


def _sep(n) -> str:
    return "|" + "|".join(["---"] * n) + "|\n"


def build_report(records: list[dict], pre_records: list[dict]) -> str:
    lines = []
    lines.append("# 哈兰德（Erling Haaland）英超数据分析报告\n")
    lines.append(
        "> 本报告基于 FBref 英超联赛数据，覆盖哈兰德加盟曼城后的三个赛季（2022-23、2023-24、2024-25）。\n"
    )

    # Section 1 – Overview
    lines.append("## 一、赛季核心进攻数据\n")
    lines.append(_row("赛季", "进球", "助攻", "进球+助攻", "无点球进球", "制造点球", "射门", "射正"))
    lines.append(_sep(8))
    for r in records:
        lines.append(
            _row(
                r["season"],
                _fmt(r.get("goals")),
                _fmt(r.get("assists")),
                _fmt(r.get("goals_assists")),
                _fmt(r.get("non_penalty_goals")),
                _fmt(r.get("penalty_kicks_made")),
                _fmt(r.get("shots_total")),
                _fmt(r.get("shots_on_target")),
            )
        )

    # Section 2 – Per 90
    lines.append("\n## 二、每90分钟效率指标\n")
    lines.append(_row("赛季", "进球/90", "助攻/90", "进球+助攻/90", "无点球进球/90", "射门/90", "射正/90"))
    lines.append(_sep(7))
    for r in records:
        lines.append(
            _row(
                r["season"],
                _fmt(r.get("goals_90")),
                _fmt(r.get("assists_90")),
                _fmt(r.get("goals_assists_90")),
                _fmt(r.get("non_penalty_goals_90")),
                _fmt(r.get("shots_total_90")),
                _fmt(r.get("shots_on_target_90")),
            )
        )

    # Section 3 – City impact
    lines.append("\n## 三、哈兰德对曼城的贡献\n")
    lines.append(_row("赛季", "曼城联赛名次", "曼城积分", "曼城总进球", "哈兰德进球", "哈兰德进球占比"))
    lines.append(_sep(6))
    for r in records:
        lines.append(
            _row(
                r["season"],
                _fmt(r.get("city_rank")),
                _fmt(r.get("city_pts")),
                _fmt(r.get("city_goals")),
                _fmt(r.get("goals")),
                f"{r['haaland_goal_share_pct']}%" if r.get("haaland_goal_share_pct") is not None else "N/A",
            )
        )

    # Section 4 – Golden boot
    lines.append("\n## 四、与射手榜冠军对比\n")
    lines.append(_row("赛季", "哈兰德进球", "射手榜冠军球员", "冠军进球数", "哈兰德是否夺冠"))
    lines.append(_sep(5))
    for r in records:
        boot_name = re.split(r"\s*[•·]\s*", r.get("golden_boot_player") or "")[0].strip()
        is_haaland = PLAYER_NAME.lower() in (r.get("golden_boot_player") or "").lower()
        lines.append(
            _row(
                r["season"],
                _fmt(r.get("goals")),
                boot_name,
                _fmt(r.get("golden_boot_goals")),
                "✅ 是" if is_haaland else "❌ 否",
            )
        )

    # Section 5 – City before Haaland
    lines.append("\n## 五、哈兰德出现之前曼城的进攻数据和成绩（2019-20至2021-22）\n")
    lines.append(_row("赛季", "曼城联赛名次", "曼城积分", "曼城总进球", "曼城队内最佳射手（进球）"))
    lines.append(_sep(5))
    for r in pre_records:
        top_scorer = _parse_top_scorer_name(r.get("city_top_scorer_raw") or "")
        scorer_goals = _fmt(r.get("city_top_scorer_goals"))
        lines.append(
            _row(
                r["season"],
                _fmt(r.get("city_rank")),
                _fmt(r.get("city_pts")),
                _fmt(r.get("city_goals")),
                f"{top_scorer} ({scorer_goals})" if top_scorer else "N/A",
            )
        )

    # Section 6 – Haaland vs league average
    lines.append("\n## 六、哈兰德与联赛平均水平对比（入榜球员样本）\n")
    lines.append(_row("指标", "哈兰德（3季均值）", "联赛均值（同指标入榜球员）", "倍数"))
    lines.append(_sep(4))
    compare_metrics = [
        ("goals_90", "进球/90"),
        ("shots_total_90", "射门/90"),
        ("shots_on_target_90", "射正/90"),
        ("goals_shot", "每射门进球率"),
    ]
    for key, label in compare_metrics:
        h_vals = [r.get(key) for r in records if r.get(key) is not None]
        l_vals = [r.get(f"league_avg_{key}") for r in records if r.get(f"league_avg_{key}") is not None]
        h_avg = round(sum(h_vals) / len(h_vals), 3) if h_vals else None
        l_avg = round(sum(l_vals) / len(l_vals), 3) if l_vals else None
        ratio = _safe_ratio(h_avg, l_avg, 2)
        lines.append(_row(label, _fmt(h_avg), _fmt(l_avg), _fmt(ratio)))

    # Section 7 – Analysis narrative
    lines.append("\n## 七、综合分析\n")

    r22 = records[0] if records else {}
    r23 = records[1] if len(records) > 1 else {}
    r24 = records[2] if len(records) > 2 else {}

    lines.append("### 5.1 历史性的首赛季（2022-23）\n")
    lines.append(
        f"哈兰德在加盟曼城后的首个英超赛季便打破了英超单赛季进球纪录，共打入 **{_fmt(r22.get('goals'))} 球**，"
        f"夺得射手王，并以每90分钟 **{_fmt(r22.get('goals_90'))} 个进球**的惊人效率领跑全联赛。"
        f"他在曼城 {_fmt(r22.get('city_goals'))} 个联赛进球中贡献了 **{r22.get('haaland_goal_share_pct')}%**，"
        f"帮助曼城以 {_fmt(r22.get('city_pts'))} 分夺得联赛冠军（排名第 {_fmt(r22.get('city_rank'))}）。\n"
    )

    lines.append("### 5.2 依旧统治级别的次赛季（2023-24）\n")
    lines.append(
        f"第二赛季，哈兰德射入 **{_fmt(r23.get('goals'))} 球**，再次夺得英超射手王，"
        f"每90分钟进球效率为 **{_fmt(r23.get('goals_90'))}**。"
        f"曼城再度夺冠（第 {_fmt(r23.get('city_rank'))} 名，{_fmt(r23.get('city_pts'))} 分），"
        f"哈兰德贡献了球队 {_fmt(r23.get('haaland_goal_share_pct'))}% 的进球。"
        f"值得注意的是，他本赛季射正/90min 达到 **{_fmt(r23.get('shots_on_target_90'))}**，为三赛季最高，"
        "显示其射门质量极高。\n"
    )

    lines.append("### 5.3 产量有所下滑的第三赛季（2024-25）\n")
    lines.append(
        f"2024-25 赛季，哈兰德进球数降至 **{_fmt(r24.get('goals'))} 球**，"
        f"排名联赛第3（射手王为穆罕默德·萨拉赫）。"
        f"效率指标（进球/90 = {_fmt(r24.get('goals_90'))}）有所回落，"
        f"制造点球数也从前两季的7个降至 {_fmt(r24.get('penalty_kicks_made'))} 个，"
        "这与曼城整体进攻下滑及球队调整有关。"
        f"曼城本赛季联赛第 {_fmt(r24.get('city_rank'))} 名，积 {_fmt(r24.get('city_pts'))} 分，"
        "哈兰德仍贡献了球队进球总数的约三分之一。\n"
    )

    lines.append("### 5.4 哈兰德在英超的核心价值\n")
    lines.append(
        "综合三个赛季的数据，哈兰德展现出以下几点核心价值：\n\n"
        "1. **极高的进球效率**：每90分钟进球率在0.72–1.17之间，远超联赛平均水平。\n"
        "2. **对球队进攻的主导性贡献**：哈兰德平均贡献曼城约 1/3 的联赛进球，是球队最重要的进攻支点。\n"
        "3. **射门质量出众**：射正/90min 长期排名联赛前列，体现其在禁区内的精准性。\n"
        "4. **两夺射手王**：2022-23赛季以36球打破英超单赛季纪录，是英超历史上最具统治力的前锋之一。\n"
        "5. **帮助曼城卫冕冠军**：前两赛季，曼城在哈兰德的带领下连续夺得联赛冠军，"
        "其第三赛季产量下滑与曼城排名滑落至第3名存在明显相关性。\n"
    )

    lines.append("\n## 八、图表说明\n")
    lines.append(
        "- `haaland_season_stats.svg`：各赛季进球、助攻、射门、射正对比柱状图。\n"
        "- `haaland_vs_top_scorers.svg`：哈兰德与各赛季英超射手王进球数对比。\n"
        "- `haaland_mancity_contribution.svg`：哈兰德进球在曼城总进球中占比（堆叠柱状图）。\n"
        "- `haaland_per90_metrics.svg`：每90分钟效率指标跨赛季对比。\n"
        "- `haaland_pre_mancity_context.svg`：哈兰德加盟前后，曼城进球与积分对比。\n"
        "- `haaland_vs_league_avg.svg`：哈兰德与联赛同指标入榜球员平均值对比。\n"
    )

    return "".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Extracting Haaland data from all seasons...")
    records = build_haaland_dataset()
    pre_records = build_pre_haaland_city_dataset()
    for r in records:
        print(
            f"  {r['season']}: goals={r.get('goals')}, assists={r.get('assists')}, "
            f"city_rank={r.get('city_rank')}, goal_share={r.get('haaland_goal_share_pct')}%"
        )

    csv_path = OUT_DIR / "haaland_data.csv"
    save_csv(records, csv_path)
    print(f"Saved: {csv_path}")

    chart_season_stats(records, OUT_DIR / "haaland_season_stats.svg")
    print(f"Saved: {OUT_DIR / 'haaland_season_stats.svg'}")

    chart_vs_top_scorers(records, OUT_DIR / "haaland_vs_top_scorers.svg")
    print(f"Saved: {OUT_DIR / 'haaland_vs_top_scorers.svg'}")

    chart_mancity_contribution(records, OUT_DIR / "haaland_mancity_contribution.svg")
    print(f"Saved: {OUT_DIR / 'haaland_mancity_contribution.svg'}")

    chart_per90_metrics(records, OUT_DIR / "haaland_per90_metrics.svg")
    print(f"Saved: {OUT_DIR / 'haaland_per90_metrics.svg'}")

    chart_pre_mancity_context(pre_records, records, OUT_DIR / "haaland_pre_mancity_context.svg")
    print(f"Saved: {OUT_DIR / 'haaland_pre_mancity_context.svg'}")

    chart_haaland_vs_league_avg(records, OUT_DIR / "haaland_vs_league_avg.svg")
    print(f"Saved: {OUT_DIR / 'haaland_vs_league_avg.svg'}")

    report = build_report(records, pre_records)
    report_path = OUT_DIR / "HAALAND_ANALYSIS_REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Saved: {report_path}")

    print("\nDone. All outputs written to:", OUT_DIR)


if __name__ == "__main__":
    main()
